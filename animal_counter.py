"""
YOLOv8 va ByteTRrack yordamida ferma hayvonlarini sanash skripti
"""

import argparse # Dasturni terminaldan turib boshqarish imkonini beradi
import cv2 # Videoni kadrlar bo'yicha o'qiydi
import requests # Python va Server o'rtasida "pochtachi" vazifasini bajaradi
import os # Kompyuteringizdagi fayllar va papkalar bilan ishlaydi
from collections import defaultdict


API_URL = "http://127.0.0.1:8000"

# Hayvonlar uchun COCO sinf identifikatori (standart yolov8n.pt modeli)
COCO_ANIMAL_CLASSES = {
    19: "cow",
    20: "sheep"
}

# Maxsus model sinf identifikatorlari (Roboflow'dan echki/qo'y/sigir modellari uchun odatiy)
CUSTOM_ANIMAL_CLASSES = {
    0: "cow",
    1: "goat",
    2: "sheep",
}

# Ranglar
COLORS = {
    "cow": (0, 165, 255),      # TO'q sariq
    "sheep": (255, 255, 0),    # Moviy rang
    "goat": (147, 20, 255),    # Pushti
    "line": (0, 255, 0),       # Yashil
    "text": (255, 255, 255),   # Oq
}

# Chiziqlarni kesib o'tish mantiqi
class LineCrossingCounter:
    """
    Gorizontal chiziqni yuqoridan pastga kesib o'tuvchi obyektlarni kuzatib boradi.

    Chiziqni kesib o'tishni aniqlash algoritmi:
    1. Har bir kuzatilgan obyektning oldingi Y holatini saqlang.
    2. Ob'ekt chiziq ustidan (prev_y < line_y) chiziqdan pastga (curr_y >= line_y) o'tganda, u kesib o'tgan bo'ladi.
    3. Har bir track_id faqat bir marta hisoblanishini ta'minlash uchun to'plamdan foydalaning.
    """

    def __init__(self, line_y: int):
        self.line_y = line_y            # Sanoq chizig'ining Y o'kidagi o'rni
        self.counted_ids = set()        # Sanab bo'lingan hayvonlar ID-lari (qayta sanamaslik uchun)
        self.prev_positions = {}        # Hayvonlarning oldingi freymdagi o'rni
        self.counts = defaultdict(int)  # Umumiy sanoq (masalan: {'cow': 5, 'sheep': 2})

    def update(self, track_id: int, center_y: int, animal_type: str) -> bool:
        """Kuzatuvchini yangilang va obyekt chiziqni kesib o'tganligini tekshiring"""

        crossed = False

        # Agar oldin o'tgan bo'lsa sanamaydi
        if track_id in self.counted_ids:
            self.prev_positions[track_id] = center_y
            return False

        # Chiziq kesib o'tilganligini tekshirish
        if track_id in self.prev_positions:
            prev_y = self.prev_positions[track_id]

            # Shart: oldin chiziqdan tepada edi (prev_y < line_y)
            # va hozir chiziqdan pastda yoki ustida (center_y >= line_y)
            if prev_y < self.line_y <= center_y:
                self.counted_ids.add(track_id)
                self.counts[animal_type] += 1
                crossed = True

        # Joriy o'rinni keyingi freym uchun saqlab qo'yamiz
        self.prev_positions[track_id] = center_y
        return crossed


# API integratsiya
def send_to_api(animal_type: str, track_id: int) -> bool:
    """Hayvonlarni aniqlashni Django serveriga yuborish"""

    payload = {
        "animal_type": animal_type,
        "track_id": track_id
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=2)
        """
        Serverga ma'lumotni yubor va javob kelishini ko'pi bilan 2 soniya kut.
        Agar 2 soniya ichida serverdan javob kelmasa (masalan, internet yomon bo'lsa yoki server qotib qolgan bo'lsa),
        kutishni to'xtat va xatolik berib, ishingni davom ettir.
        """

        if response.status_code == 201:
            print(f"Muvaffaqiyatli saqlandi: {animal_type} (Id: {track_id})")
            return True

        elif response.status_code == 400:
            print(f"noto'g'ri so'rov xabari: {animal_type} (Id: {track_id})")
            return False
        else:
            print(f"Xatolik: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"[API] Ulanish amalga oshmadi - server ishlamayaptimi?")
        return False
    except requests.exceptions.Timeout:
        print(f"[API] So'rov vaqti tugadi")
        return False
    except Exception as e:
        print(f"[API] Xatolik: {e}") # Server o'chiq bo'lsa xato beradi
        return False


# Modelni o'qish

def load_model(model_path: str, use_roboflow: bool = False, api_key: str = None):
    from ultralytics import YOLO

    if use_roboflow:
        print("[INFO] Roboflow’dan model yuklanmoqda...")
        try:
            from roboflow import Roboflow

            if not api_key:
                raise ValueError("Roboflow API kaliti talab qilinadi. --api-key YOUR_KEY dan foydalaning")

            rf = Roboflow(api_key=api_key)

            # Standart: echki-qo'y-sigirni aniqlash modeli
            project = rf.workspace().project("goat-sheep-and-cow-detection")
            model = project.version(1).model

            print("Roboflow modeli muvaffaqiyatli yuklandi!")
            return model, "roboflow"

        except ImportError:
            print("Roboflow o'rnatilmagan. Ishga tushirish: pip install roboflow")
            raise
        except Exception as e:
            print(f"Roboflow modelini yuklashda xatolik yuz berdi: {e}")
            raise

    else:
        # Mahalliy YOLO modelini yuklash
        print(f"Roboflow modelni yuklash: {model_path}")

        if not os.path.exists(model_path) and model_path != "yolov8n.pt":
            print(f"Model fayli topilmadi: {model_path}")
            print("yolov8 modeli yuklanmoqda...")
            model_path = "yolov8n.pt"

        model = YOLO(model_path)
        print("Modelni yuklash muvaffaqiyatli yuklandi!")
        return model, "yolo"


def get_class_mapping(model, use_custom:bool, model_type: str):
    """Model turiga asoslangan holda hayvon nomini aniqlash uchun sinf identifikatorini olish."""

    if model_type == "roboflow":
        return CUSTOM_ANIMAL_CLASSES

    if use_custom:
        try:
            names = model.names
            print(f"MOdel sinflari: {names}")

            animals_classes = {}
            for class_id, name in names.items():
                name_lower = name.lower()
                if name_lower in ["cow", "sheep", "goat"]:
                    animals_classes[class_id] = name_lower

            if animals_classes:
                print(f"Aniqlangan hayvonlar sinfi: {animals_classes}")
                return animals_classes
            else:
                print("Modelda hech qanday ferma hayvonlari topilmadi.")
                return CUSTOM_ANIMAL_CLASSES

        except Exception as e:
            print(f"Model sinflarini o'qib bo'lmadi: {e}")
            return CUSTOM_ANIMAL_CLASSES

    else:
        return COCO_ANIMAL_CLASSES


def draw_detections(frame, boxes, track_ids, class_ids, counter: LineCrossingCounter, animals_classes: dict):
    hieght, width = frame.shape[:2]

    # Sanoq chizig'ini chizish
    cv2.line(frame, (0, counter.line_y), (width, counter.line_y), COLORS["line"], 2)
    cv2.putText(frame, "COUNTING LINE", (10, counter.line_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLORS["line"], 2)

    # Topilgan har bir hayvonni aylana bo'ylab tekshirish
    for box ,track_id, class_id in zip(boxes, track_ids, class_ids):
        if class_id not in animals_classes:
            continue

        animal_type = animals_classes[class_id]
        color = COLORS.get(animal_type, (0, 255, 0))

        # Kordinatalarini olish
        x1, y1, x2, y2 = map(int, box[:4])
        center_y = (y1 + y2) // 2

        # Hayvon atrofida ramka chizish
        thickness = 3 if track_id in counter.counted_ids else 2
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

        # Hayvon turi va ID-sini yozish (masalan: cow #12)
        label = f"{animal_type} #{track_id}"
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.2, 2)
        cv2.rectangle(frame, (x1, y1 - 25), (x1 + label_size[0], y1), color, -1)
        cv2.putText(frame, label, (x1, y1 - 7),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        # Markaziy nuqtani chizish
        center_x = (x1 + x2) // 2
        cv2.circle(frame, (center_x, center_y), 5, color, -1)

    # Ekranning chap tomoniga umumiy hisob-kitobni chiqarish
    y_offset = 30
    cv2.putText(frame, "ANIMAL COUNT", (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, COLORS["text"], 2)

    for animal_type, count in counter.counts.items():
        y_offset += 35
        color = COLORS.get(animal_type, COLORS["text"])
        cv2.putText(frame, f"{animal_type.upper()}: {count}", (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)


    y_offset += 40
    total = sum(counter.counts.values())
    cv2.putText(frame, f"Jami: {total}", (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, COLORS["text"], 2)

    return frame


def process_video(source, model_path: str = "yolov8n.pt", line_position: float = 0.6,
                  use_custom: bool = False, use_roboflow: bool = False, api_key: str = None):

    # Modelni va uning turini yuklab oladi (YOLO yoki Roboflow)
    model, model_type = load_model(model_path, use_roboflow, api_key)

    # Model qaysi raqamda qaysi hayvonni tanishini aniqlaydi (Mapping)
    animal_classes = get_class_mapping(model, use_custom, model_type)
    print(f"Kuzatuv: {animal_classes}")

    # Videoni ochadi (Kamera yoki fayl bo'lishi mumkin)
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"Xatolik. video faylni ochmadi: {source}")
        return

    # Videoning o'lchamlari va FPS (tezligi)ni oladi
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30

    # Sanoq chizig'ining joylashgan o'rnini (Y o'qi bo'yicha) hisoblaydi
    # Masalan, line_position=0.6 bo'lsa, chiziq ekranning 60% pastrog'ida bo'ladi
    line_y = int(height * line_position)

    # Sanoq ob'ektini (Counter) yaratadi
    counter = LineCrossingCounter(line_y)

    print(f"Video: {width}x{height} @ {fps} fps")
    print(f"sanash chiziqi: Y={line_y}")
    print("Chiqish uchun 'q', qaytadan boshlash uchun 'r'")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Video yoki kamera uzuldi!")
            break

        # YOLO Tracking (ByteTrack algoritmi orqali)
        # persist=True - bu hayvonni kadrlar o'zgarsa ham tanib qolishni ta'minlaydi
        results = model.track(frame, persist=True, tracker="bytetrack.yaml", classes=list(animal_classes.keys()) if not use_custom else None, verbose=False)


        # Agar kadrda birorta ob'ekt topilgan bo'lsa:
        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()  # Koordinatalar
            track_ids = results[0].boxes.id.int().cpu().numpy()  # Hayvon ID raqamlari
            class_ids = results[0].boxes.cls.int().cpu().numpy()  # Hayvon turlari

            # Topilgan har bir hayvonni birma-bir tekshiramiz
            for box, track_id, class_id in zip(boxes, track_ids, class_ids):
                if class_id not in animal_classes:
                    continue

                animal_type = animal_classes[class_id]
                center_y = int((box[1] + box[3]) / 2)  # Hayvon markazi

                # Agar hayvon chiziqdan o'tgan bo'lsa:
                if counter.update(track_id, center_y, animal_type):
                    print(f"[COUNT] {animal_type} #{track_id} o'tdi!")
                    send_to_api(animal_type, int(track_id))  # API-ga yuboramiz

            # Ekranga chizmalarni (ramka, chiziq, statistika) chiqaramiz
            frame = draw_detections(frame, boxes, track_ids, class_ids, counter, animal_classes)
        else:
            # Agar hech narsa topilmasa ham, shunchaki chiziqni chizib turamiz
            cv2.line(frame, (0, line_y), (width, line_y), COLORS["line"], 2)

        # Tasvirni ekranda ko'rsatish
        cv2.imshow("Farm Animal Counter", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):  # 'q' tugmasi bosilsa - chiqish
            break
        elif key == ord('r'):  # 'r' bosilsa - sanoqni nolga tushirish (reset)
            counter = LineCrossingCounter(line_y)

    # Tozalash (Kamera va derazalarni yopish)
    cap.release()
    cv2.destroyAllWindows()

    # Terminalda yakuniy statistikani ko'rsatish
    print("\nYAKUNIY HISOB:")
    for animal_type, count in counter.counts.items():
        print(f"  {animal_type}: {count}")


if __name__ == "__main__":
    # rgumentlar ob'ektini yaratish
    parser = argparse.ArgumentParser(description="Virtual chiziqdan o'tayotgan ferma hayvonlarini sanash",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
    Misollar:
        # Standart COCO modeli (faqat sigirlar va qo'ylar uchun):
        python animal_counter.py --source video.mp4
        
        # Echki qo'llab-quvvatlashi bilan maxsus model:
        python animal_counter.py --source video.mp4 --model goat_model.pt --custom
        
        # Roboflow modeli:
        python animal_counter.py --source video.mp4 --roboflow --api-key YOUR_KEY
        """
    )

    parser.add_argument("--source", type=str, default="0", help="Video fayl yo'li yoki kamera indeksi (standart: veb-kamera uchun 0)")

    parser.add_argument("--model", type=str, default="yolov8n.pt", help="YOLO model fayliga yo'l (standart: yolov8n.pt)")

    parser.add_argument("--line", type=float, default=0.6, help="Sanoq chizig'ining joylashuvi, balandlikka nisbatan ulushda (standart: 0.6)")

    parser.add_argument("--custom", action="store_true", help="COCO bo'lmagan modellar uchun maxsus klasslardan (echki/qo'y/sigir) foydalanish")

    parser.add_argument("--roboflow", action="store_true", help="Modelni Roboflow-dan yuklab olish (--api-key talab qilinadi)")

    parser.add_argument("--api-key", type=str, default=None, help="Modellarni yuklash uchun Roboflow API kaliti")

    # Foydalanuvchi terminalda yozgan barcha buyruqlarni yig'ib oladi
    args = parser.parse_args()

    # Source'ni tekshirish:
    # Agar foydalanuvchi "0" yoki "1" deb yozsa, uni songa (integer) aylantiradi (kamera uchun)
    # Agar "video.mp4" deb yozsa, u matn (string) holida qoladi
    source = int(args.source) if args.source.isdigit() else args.source

    # ASOSIY JARAYONNI BOSHLASH
    # Yuqorida yig'ilgan barcha sozlamalarni process_video funksiyasiga uzatadi
    process_video(source=source, model_path=args.model, line_position=args.line, use_custom=args.custom, use_roboflow=args.roboflow, api_key=args.api_key)