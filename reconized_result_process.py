import stable_whisper as whisper


def plain_text_result(result: whisper.WhisperResult):
    """
    获取识别结果的纯文本信息
    并且包含断句换行
    """
    # logger.info(result)

    ori_dict = result.ori_dict if type(
        result) == whisper.WhisperResult else result
    segs = ori_dict.get("segments")
    plain_texts = []

    assert segs is not None

    for para in segs:
        plain_texts.append(
            para.get("text")
        )

    return '\n'.join(plain_texts)
