from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import os
from multiprocessing import Pool
from multiprocessing.managers import BaseManager
from tqdm import tqdm
import warnings
from blueprints import Image, OCR

warnings.filterwarnings("ignore", category=UserWarning)
model = ocr_predictor(
    det_arch="db_resnet50", reco_arch="crnn_vgg16_bn", pretrained=True
)


class SimpleClass(object):
    def __init__(self):
        self.model = model

    def set(self, value):
        self.var = value

    def get(self):
        return self.var


def normalize(points: list, width: int, height: int) -> list:
    x0, y0, x2, y2 = [int(p) for p in points]

    x0 = int(1000 * (x0 / width))
    x2 = int(1000 * (x2 / width))
    y0 = int(1000 * (y0 / height))
    y2 = int(1000 * (y2 / height))

    return [x0, y0, x2, y2]


def apply_ocr(image_path, output_file_path, write_to_file=True, normalize_bbox=False):
    # print("Applying OCR on", image_path)
    # model = ocr_predictor(
    #     det_arch="db_resnet50", reco_arch="crnn_vgg16_bn", pretrained=True
    # )
    # Read image
    img = DocumentFile.from_images(image_path)
    # Apply OCR
    pred = model(img)

    # pred.show(img)

    # output image data as file
    export = pred.export()
    height, width = export["pages"][0]["dimensions"]
    # Flatten the export
    page_words = [
        [
            word
            for block in page["blocks"]
            for line in block["lines"]
            for word in line["words"]
        ]
        for page in export["pages"]
    ]
    page_dims = [page["dimensions"] for page in export["pages"]]
    # Get the coords in [xmin, ymin, xmax, ymax]
    words_abs_coords = [
        [
            [
                int(round(word["geometry"][0][0] * dims[1])),
                int(round(word["geometry"][0][1] * dims[0])),
                int(round(word["geometry"][1][0] * dims[1])),
                int(round(word["geometry"][1][1] * dims[0])),
            ]
            for word in words
        ]
        for words, dims in zip(page_words, page_dims)
    ]
    if not write_to_file:
        bboxes = []
        for i, word in enumerate(page_words[0]):
            value = word["value"]
            bbox = words_abs_coords[0][i]
            [lx, ly, rx, ry] = (
                normalize(bbox, width, height) if normalize_bbox else bbox
            )
            bboxes.append({"value": value, "bbox": [lx, ly, rx, ry]})
        return bboxes

    with open(output_file_path, "w") as f:
        for i, word in enumerate(page_words[0]):
            value = word["value"]
            bbox = words_abs_coords[0][i]
            [lx, ly, rx, ry] = (
                normalize(bbox, width, height) if normalize_bbox else bbox
            )
            f.write(f"{value}\t{lx} {ly} {rx} {ry}\n")
    return 0


def ocr_complete_dir(
    images_dir_path: str, output_dir_path: str, show_progress: bool = True
):

    """Applies OCR to all images in a directory and saves the output to a directory"""

    if not os.path.exists(output_dir_path):
        os.makedirs(output_dir_path)
    files = []
    for file in os.listdir(images_dir_path):
        if file.endswith(".jpg") or file.endswith(".png"):
            files.append(file)
    if show_progress:
        for _ in tqdm(
            map(
                apply_ocr_star,
                [
                    (
                        os.path.join(images_dir_path, file),
                        os.path.join(output_dir_path, file[:-4] + ".txt"),
                    )
                    for file in files
                ],
            ),
            desc="Applying OCR",
            total=len(files),
        ):
            pass
    else:
        for file in files:
            apply_ocr(
                os.path.join(images_dir_path, file),
                os.path.join(output_dir_path, file[:-4] + ".txt"),
            )


def apply_ocr_star(args):
    """Just to unpack the arguments for apply_ocr"""
    apply_ocr(args[0], args[1])
    return 1
    # a = str(1)
    # for i in range(10000000):
    #     a = a + str(i)
    #     if i % 100000 == 0:
    #         a = "0"
    # # print(k)
    # return 0


def ocr_complete_dir_parallel(
    images_dir_path: str,
    output_dir_path: str,
    pool_size: int = 4,
    show_progress: bool = True,
):

    """Applies OCR to all images using multiprocessing feature in a directory and
    saves the output to a directory"""

    if not os.path.exists(output_dir_path):
        os.makedirs(output_dir_path)
    files = []
    for file in os.listdir(images_dir_path):
        if file.endswith(".jpg") or file.endswith(".png"):
            files.append(file)

    # BaseManager.register("SimpleClass", SimpleClass)
    # manager = BaseManager()
    # manager.start()
    # inst = manager.SimpleClass()
    # model.

    with Pool(pool_size) as p:
        if show_progress:
            # print("Here")
            for _ in tqdm(
                p.imap_unordered(
                    apply_ocr_star,
                    [
                        (
                            os.path.join(images_dir_path, file),
                            os.path.join(output_dir_path, file[:-4] + ".txt"),
                        )
                        for file in files
                    ],
                ),
                desc="Applying OCR",
                total=len(files),
            ):
                pass
        else:
            for file in files:
                apply_ocr(
                    os.path.join(images_dir_path, file),
                    os.path.join(output_dir_path, file[:-4] + ".txt"),
                )


# Read words from file
def perform_ocr_and_save(db, image_id):
    image = db.query(Image).filter(Image.id == image_id).first()
    bboxes = apply_ocr(
        "uploaded_images/" + image.path,
        "",
        write_to_file=False,
        normalize_bbox=True,
    )
    ocred_words = []
    for item in bboxes:
        if item["value"].strip() == "":
            continue

        ocred_words.append(
            OCR(
                text=item["value"],
                posx_0=item["bbox"][0],
                posy_0=item["bbox"][1],
                posx_1=item["bbox"][2],
                posy_1=item["bbox"][3],
                image_id=image.id,
            )
        )

    db.add_all(ocred_words)
    db.commit()
    # return words
    return db.query(OCR).filter_by(image_id=image_id).all()


if __name__ == "__main__":
    apply_ocr("sample.jpg", "./ocr_outputs/sample.txt")
