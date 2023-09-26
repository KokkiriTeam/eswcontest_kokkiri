import os
import subprocess
import json
import openai
import time
import pyaudio
import wave
import audioop
import gcp_tts
import sms
from dotenv import load_dotenv


def mayday_112():                          # Twilio API를 이용해서 112에 문자 메시지 신고
    sms.send_sms_112(112)
    os.system("mpg123 ./sound/success.mp3")
    print('112 신고')
    return


def mayday_119():                          # Twilio API를 이용해서 119에 문자 메시지 신고
    sms.send_sms_119(119)
    os.system("mpg123 ./sound/success.mp3")
    print('119 신고')
    return


def voice_rec():
    po = pyaudio.PyAudio()                               # 녹음 기능을 위한 pyaudio 초기화
    for index in range(po.get_device_count()):
        desc = po.get_device_info_by_index(index)
        # if desc["name"] == "record":
        print("DEVICE: %s  INDEX:  %s  RATE:  %s " % (desc["name"], index, int(desc["defaultSampleRate"])))

    FORMAT = pyaudio.paInt16
    CHANNELS = 1                                      # 모노 음성
    RATE = 44100                                      # 전송률
    CHUNK = 640                                       # 전송 단위 크기
    RECORD_SECONDS = 7                                # 녹음 시간
    WAVE_OUTPUT_FILENAME = "./sound/question.wav"       # 녹음 생성 오디오 파일

    audio = pyaudio.PyAudio()

    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    frames = []
    sound_volume = 3000

    os.system("mpg123 ./sound/rec.mp3")  # 음성 녹음 시작 안내 메시지
    print("---음성 녹음 시작---")

    while True:
        data = stream.read(CHUNK)
        rms = audioop.rms(data, 2)
        if rms > sound_volume:                 # 마이크에 기준 볼륨보다 큰 소리가 들어오면 녹음 작동
            frames.append(data)
            for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK)
                frames.append(data)
            data = stream.read(CHUNK)
            rms = audioop.rms(data, 2)
            if rms < 1500:                     # 큰 소리가 들어오지 않으면 녹음 종료
                break
            else:
                continue

    print("---음성 녹음 완료---")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')        # question.wav 파일 생성
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()

    time.sleep(0.1)


def chat_gpt_speak():
    load_dotenv()
    openai.organization = "org-oMb8n1ArLu6XkrsXxXNg9hQQ"                    # OpenAI API를 사용하기 위한 키값들 초기화
    openai.api_key = os.getenv("OPENAI_API_KEY")                            # .env 파일에 작성한 API 키 가져오기
    openai.Model.list()

    for cmd in [""" curl https://api.openai.com/v1/audio/transcriptions \
                  -H "Authorization: Bearer $OPENAI_API_KEY" \
                  -H "Content-Type: multipart/form-data" \
                  -F file="@./sound/question.wav" \
                  -F model="whisper-1" """]:                                         # OpenAI Speech to text API에 질문 파일인 question.wav 파일 전송 후 결과 값 수신

        words = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()     # 결과 값(음성을 텍스트로 바꾼 값)을 json으로 되돌려 받은 후 질문 문자열만 추출
        json_list = json.loads(words)

        speech_text = json_list["text"]

        print(json_list["text"])

    if '경찰' in speech_text and '도와줘' in speech_text:                              # 만약 녹음 내용이 구조 요청이면 구조 메시지 전송 함수를 실행
        mayday_112()
    elif '소방관' in speech_text and '도와줘' in speech_text:
        mayday_119()
    else:
        conversation.append({"role": "user", "content": speech_text})       # 구조 요청이 아닐 경우 ChatGPT에게 질문함
        response = openai.ChatCompletion.create(
            model="gpt-4",                                                  # ChatGPT 버전이 최근 gpt-3-turbo에서 gpt-4로 업그레이드 됨
            messages=conversation
        )

        answer = response.choices[0]["message"]["content"].strip()         # 문자열로 응답을 받음
        print(answer)

        gcp_tts.synthesize_text(answer)

        conversation.append({"role": "assistant", "content": response['choices'][0]['message']['content']})  # ChatGPT가 답변 후 재질문 받는 기능을 위한 코드


if __name__ == "__main__":
    os.system("mpg123 ./sound/start.mp3")        # 스피커 시작 멘트
    time.sleep(2)
    conversation = [{"role": "system", "content": "You are a helpful assistant."}]      # ChatGPT System 초기화
    while True:
        voice_rec()   # 질문 음성 녹음
        chat_gpt_speak()  # ChatGPT 답변
