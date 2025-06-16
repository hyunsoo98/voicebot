import streamlit as st

# audiocorder 패키지 대신 streamlit_audio_recorder 사용
# from audiorecorder import audiorecorder # 이 줄은 더 이상 필요 없음
from streamlit_audio_recorder import st_audiorec # 오류 메시지에 따른 임포트

import openai
import os
from datetime import datetime
from gtts import gTTS
import base64


###### 기능 구현 함수 ######
def STT(audio, apikey):
    #파일 저장
    filename='input.mp3'
    # audio.export(filename, format="mp3") # audiorecorder 패키지의 export 메서드 사용 시
    # st_audiorec는 다른 방식으로 오디오 데이터를 가져와야 할 수 있습니다.
    # 여기서는 audio 객체가 raw audio data를 포함한다고 가정합니다.
    with open(filename, "wb") as f:
        f.write(audio) # st_audiorec의 return 값에 따라 수정 필요
    
    #음원 파일 열기
    audio_file = open(filename, "rb")
    #whisper 모델을 활용해 텍스트 얻기
    client = openai.OpenAI(api_key=apikey)
    respons = client.audio.transcriptions.create(model="whisper-1",file=audio_file)
    audio_file.close()
    
    #파일 삭제
    os.remove(filename)
    return respons.text

def ask_gpt(prompt, model, apikey):
    client = openai.OpenAI(api_key=apikey)
    response = client.chat.completions.create(
        model=model,
        messages=prompt)
    gptResponse = response.choices[0].message.content
    return gptResponse

def TTS(response):
    #gTTS를 활용하여 음성 파일 생성
    filename = "output.mp3"
    tts = gTTS(text=response, lang="ko")
    tts.save(filename)
    
    #음원 파일 자동 재생
    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
        <audio autoplay="True">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
    st.markdown(md, unsafe_allow_html=True)

    # 파일 삭제
    os.remove(filename)

# #### 메인 함수 #####
def main():
    # 기본 설정
    st.set_page_config(
        page_title="음성 비서 프로그램",
        layout="wide"
    )

    # 제목
    st.header("음성 비서 프로그램")

    # 구분선
    st.markdown("---")
    
    # 기본 설명
    with st.expander("음성비서 프로그램에 관하여", expanded=True):
        st.write(
            """
- 음성 비서 프로그램의 UI는 스트림릿을 활용했습니다.
- STT(Speech-To-Text)는 OpenAI의 Whisper AI를 활용했습니다.
- 답변은 OpenAI의 GPT 모델을 활용했습니다.
- TTS(Text-To-Speech)는 구글의 Google Translate TTS를 활용했습니다.
            """
        )

    # session state 초기화
    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    if "OPENAI_API" not in st.session_state:
        st.session_state["OPENAI_API"] = ""

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system", "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in korea"}]

    if "check_audio" not in st.session_state:
        st.session_state["check_reset"] = False
        
    # 사이드바 생성
    with st.sidebar:
        # Open AI API 키 입력받기
        st.session_state["OPENAI_API"] = st.text_input(label="OPENAI API 키", placeholder="Enter Your API Key", value="", type="password")

        st.markdown("---")

        # GPT 모델을 선택하기 위한 라디오 버튼 생성
        model = st.radio(label="GPT 모델", options=["gpt-4", "gpt-3.5-turbo"])

        st.markdown("---")

        # 리셋 버튼 생성
        if st.button(label="초기화"):
            # 리셋 코드
            st.session_state["chat"] = []
            st.session_state["messages"] = [{"role": "system", "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in korea"}]
            st.session_state["check_reset"] = True # 리셋 버튼 클릭 시 플래그 설정
            st.rerun() # 앱을 다시 실행하여 변경사항 반영
        st.markdown("---")
        
    # 기능 구현 공간
    col1, col2 = st.columns(2)
    with col1:
        #왼쪽 영역 작성
        st.subheader("질문하기")
        #음성 녹음 아이콘 추가 (st_audiorec 사용)
        # audiorecorder 대신 st_audiorec를 사용합니다.
        # st_audiorec는 다른 리턴 값을 가질 수 있으므로 사용법을 확인해야 합니다.
        # 예를 들어, 오디오 바이트를 직접 반환할 수 있습니다.
        # 아래는 st_audiorec 사용 예시입니다.
        wav_audio_data = st_audiorec() # st_audiorec()는 녹음된 오디오 데이터를 반환합니다.

        # audio = audiorecorder("클릭하여 녹음하기", "녹음 중...") # 이전 audiorecorder 패키지 사용 시

        if wav_audio_data is not None and (st.session_state["check_reset"] == False): # 녹음을 실행하면?
            # 음성 재생 (st_audiorec는 자체 재생 기능을 제공하거나 raw data를 반환)
            st.audio(wav_audio_data, format='audio/wav') # st_audiorec의 반환 형식에 맞춤

            #음원 파일에서 텍스트 추출
            # STT 함수에 맞게 wav_audio_data를 처리합니다.
            # audiorecorder의 audio 객체와 st_audiorec의 wav_audio_data는 형식이 다를 수 있습니다.
            # STT 함수 내부에서 audio.export() 대신 wav_audio_data를 직접 파일로 저장합니다.
            question = STT_with_bytes(wav_audio_data, st.session_state['OPENAI_API'])
            
            #채팅을 시각화하기 위해 질문 내용 저장
            now = datetime.now().strftime("%H:%M")
            st.session_state['chat'] = st.session_state['chat'] + [("user", now, question)]
            
            #gpt 모델에 넣을 프롬프트를 위해 질문 내용 저장
            st.session_state['messages'] = st.session_state['messages'] + [{"role":"user","content": question}]
            
            # 리셋 플래그 재설정 (오디오가 처리된 후)
            st.session_state["check_reset"] = False # 오디오가 처리된 후 리셋 플래그를 다시 False로 설정

    with col2:
        #오른쪽 영역 작성
        st.subheader("질문/답변")
        if (st.session_state["check_reset"] == False): # audiorecorder 대신 st_audiorec 사용 시 조건 조정
            # ChatGPT에게 답변 얻기
            response = ask_gpt(st.session_state["messages"], model,
                                st.session_state["OPENAI_API"])

            # GPT 모델에 넣을 프롬프트를 위해 답변 내용 저장
            st.session_state["messages"] = st.session_state["messages"] + [{"role":"system", "content": response}]

            # 채팅 시각화를 위한 답변 내용 저장
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"] + [("bot", now, response)]

            #채팅 형식으로 시각화하기
            for sender, time, message in st.session_state["chat"]:
                if sender == "user":
                    st.write(f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                    st.write("") # This looks like an empty line, might be for spacing

                else:
                    st.write(f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:lightgray;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                    st.write("") # This looks like an empty line, might be for spacing
            
            #gTTS를 활용하여 음성 파일 생성 및 재생
            TTS(response)

# STT 함수를 st_audiorec의 반환값에 맞게 수정
def STT_with_bytes(audio_bytes, apikey):
    #파일 저장
    filename='input.wav' # st_audiorec는 보통 wav 형식의 바이트를 반환합니다.
    with open(filename, "wb") as f:
        f.write(audio_bytes)
    
    #음원 파일 열기
    audio_file = open(filename, "rb")
    #whisper 모델을 활용해 텍스트 얻기
    client = openai.OpenAI(api_key=apikey)
    respons = client.audio.transcriptions.create(model="whisper-1",file=audio_file)
    audio_file.close()
    
    #파일 삭제
    os.remove(filename)
    return respons.text


if __name__ == "__main__":
    main()
