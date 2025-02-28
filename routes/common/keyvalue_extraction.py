def extract_keyvalue(file_path: str, image_id: int):
    if image_id == 1:
        annotation_process = [
            {
                "key": "13 name",
                "key_bbox": [1,2,3,4],
                "value": "ashim",
                "value_bbox": [5,6,7,8],
            }
        ]
    elif image_id == 2:
        annotation_process = [
            {
                "key": "x name",
                "key_bbox": [1,2,3,4],
                "value": "sabin",
                "value_bbox": [5,6,7,8],
            }
        ]
    elif image_id == 3:
        annotation_process = [
            {
                "key": "10 name",
                "key_bbox": [1,2,3,4],
                "value": "anil",
                "value_bbox": [5,6,7,8],
            }
        ]
    if image_id == 4:
        annotation_process = [
            {
                "key": "11 name",
                "key_bbox": [1,2,3,4],
                "value": "anmol",
                "value_bbox": [5,6,7,8],
            }
        ]
    return annotation_process