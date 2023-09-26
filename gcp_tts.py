import os
from google.cloud import texttospeech


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./eswcontest-kokkiri-f8a71970be32.json"


def synthesize_text(text):
    client = texttospeech.TextToSpeechClient()

    # 최대 길이를 200으로 지정 (지나치게 길어지면 에러 발생)
    max_length = 200
    # . 단위로 문장 분리
    words = text.split('. ')
    sentences = []
    current_sentence = ''
    for word in words:
        if len(current_sentence + word) <= max_length:
            current_sentence += word + ' '
        else:
            sentences.append(current_sentence.strip() + '.')
            current_sentence = word + ' '
    if current_sentence:
        sentences.append(current_sentence.strip() + '.')

    # 빈 배열 생성
    audio_data = []

    # 문장 개수 단위로 텍스트 변환
    for sentence in sentences:
        input_text = texttospeech.SynthesisInput(text=sentence)

        voice = texttospeech.VoiceSelectionParams(
            language_code="ko-KR",
            name="ko-KR-Neural2-B",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            request={"input": input_text, "voice": voice, "audio_config": audio_config}
        )

        audio_data.append(response.audio_content)

    audio_data = b"".join(audio_data)

    with open("./sound/answer.mp3", "wb") as out:
        out.write(audio_data)
        print('오디오 파일 생성')

    os.system("mpg123 ./sound/answer.mp3")

