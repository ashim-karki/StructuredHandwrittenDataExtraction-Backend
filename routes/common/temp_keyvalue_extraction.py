def extract_keyvalue(file_path: str, image_id: int):
    if image_id == 1:
        annotation_process = [
            {
                "key": "13 name",
                "key_bbox": [1,2,3,4],
                "value": """THIS IS A PARAGRAPH ashim is a good boy. he is also a bad boy.
                he is friend with anil paudel.
                i don't know what he is like but people say that he is also a very good bad boy.""",
                "value_bbox": [5,6,7,8],
            },
            {
                "key": "13 second name",
                "key_bbox": [1,2,3,4],
                "value": "This is for testing purpose of bad boys api",
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