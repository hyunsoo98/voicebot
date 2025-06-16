##### 기본 정보 입력 #####
import streamlit as st
# audiorecorder 패키지 추가
from audiorecorder import audiorecorder
# OpenAI 패키지 추가
import openai
# 파일 삭제를 위한 패키지 추가
import os
# 시간 정보를 위한 패키지 추가
from datetime import datetime
# TTS 패키기 추가
from gtts import gTTS
# 음원 파일 재생을 위한 패키지 추가
import base64

##### 기능 구현 함수 #####
def STT(audio):
    # 파일 저장
    filename='input.mp3'
    audio.export(filename, format="mp3")
    # 음원 파일 열기
    audio_file = open(filename, "rb")
    # Whisper 모델을 활용해 텍스트 얻기
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    audio_file.close()
    # 파일 삭제
    os.remove(filename)
    return transcript["text"]

def ask_gpt(prompt, model):
    response = openai.ChatCompletion.create(model=model, messages=prompt)
    system_message = response["choices"][0]["message"]
    return system_message["content"]

def TTS(response):
    # gTTS 를 활용하여 음성 파일 생성
    filename = "output.mp3"
    tts = gTTS(text=response,lang="ko")
    tts.save(filename)

    # 음원 파일 자동 재생생
    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="True">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md,unsafe_allow_html=True,)
    # 파일 삭제
    os.remove(filename)

##### 메인 함수 #####
def main():
    # 기본 설정
    st.set_page_config(
        page_title="음성 비서 프로그램",
        layout="wide")

    # session state 초기화
    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system", "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in korea"}]

    if "check_reset" not in st.session_state:
        st.session_state["check_reset"] = False
    
    # 새로운 세션 상태 추가
    if "last_audio_processed" not in st.session_state:
        st.session_state["last_audio_processed"] = False

    # 제목
    st.header("음성 비서 프로그램")
    # 구분선
    st.markdown("---")

    # 기본 설명
    with st.expander("음성비서 프로그램에 관하여", expanded=True):
        st.write(
        """
        - 음성비서 프로그램의 UI는 스트림릿을 활용했습니다.
        - STT(Speech-To-Text)는 OpenAI의 Whisper AI를 활용했습니다.
        - 답변은 OpenAI의 GPT 모델을 활용했습니다.
        - TTS(Text-To-Speech)는 구글의 Google Translate TTS를 활용했습니다.
        """
        )

        st.markdown("")

    # 사이드바 생성
    with st.sidebar:

        # Open AI API 키 입력받기
        openai.api_key = st.text_input(label="OPENAI API 키", placeholder="Enter Your API Key", value="", type="password")

        st.markdown("---")

        # GPT 모델을 선택하기 위한 라디오 버튼 생성
        model = st.radio(label="GPT 모델",options=["gpt-4", "gpt-3.5-turbo"])

        st.markdown("---")

        # 리셋 버튼 생성
        if st.button(label="초기화"):
            # 리셋 코드
            st.session_state["chat"] = []
            st.session_state["messages"] = [{"role": "system", "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in korea"}]
            st.session_state["check_reset"] = True # 리셋 버튼 클릭 시 True로 설정
            st.session_state["last_audio_processed"] = False # 마지막 오디오 처리 상태 초기화
            st.rerun() # 상태를 즉시 반영하기 위해 rerun

    # 기능 구현 공간
    col1, col2 = st.columns(2)
    with col1:
        # 왼쪽 영역 작성
        st.subheader("질문하기")
        # 음성 녹음 아이콘 추가
        audio = audiorecorder("클릭하여 녹음하기", "녹음중...")

        # 리셋 버튼이 눌리지 않았고, audio 객체가 존재하며, duration_seconds 속성이 있고, 녹음 길이가 0보다 클 때만 처리
        # hasattr()을 추가하여 audio.duration_seconds 접근 전에 속성 존재 여부 확인
        if audio is not None and hasattr(audio, 'duration_seconds') and audio.duration_seconds > 0 and not st.session_state["check_reset"]:
            # 음성 재생
            st.audio(audio.export().read())
            # 음원 파일에서 텍스트 추출
            question = STT(audio)

            # 채팅을 시각화하기 위해 질문 내용 저장
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"].append(("user",now, question))
            # GPT 모델에 넣을 프롬프트를 위해 질문 내용 저장
            st.session_state["messages"].append({"role": "user", "content": question})

            st.session_state["last_audio_processed"] = True # 음성이 성공적으로 처리되었음을 표시
            st.rerun() # 질문 처리 후 바로 답변을 위해 rerun
        elif st.session_state["check_reset"]: # 리셋 버튼이 눌렸을 때
            st.session_state["check_reset"] = False # 리셋 상태 해제
            st.session_state["last_audio_processed"] = False # 마지막 오디오 처리 상태 초기화
            # st.rerun()은 이미 리셋 버튼 클릭 시 호출했으므로 여기서는 생략

    with col2:
        # 오른쪽 영역 작성
        st.subheader("질문/답변")

        # 채팅 기록이 있을 때만 시각화
        if st.session_state["chat"]:
            # 마지막 질문이 사용자 질문이고, 아직 답변이 없으며, 마지막 오디오가 처리되었다면 답변 생성
            if st.session_state["last_audio_processed"] and st.session_state["chat"][-1][0] == "user":
                with st.spinner("GPT가 답변을 생성중입니다..."):
                    # ChatGPT에게 답변 얻기
                    response = ask_gpt(st.session_state["messages"], model)

                # GPT 모델에 넣을 프롬프트를 위해 답변 내용 저장
                st.session_state["messages"].append({"role": "system", "content": response})

                # 채팅 시각화를 위한 답변 내용 저장
                now = datetime.now().strftime("%H:%M")
                st.session_state["chat"].append(("bot",now, response))

                st.session_state["last_audio_processed"] = False # 답변이 생성되었으므로 초기화
                st.rerun() # 답변 생성 후 채팅창 업데이트를 위해 rerun


            # 채팅 형식으로 시각화 하기 (항상 최신 채팅 기록을 보여줌)
            for sender, time, message in st.session_state["chat"]:
                if sender == "user":
                    st.write(f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                    st.write("")
                else:
                    st.write(f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:lightgray;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                    st.write("")
                    # 봇의 답변이 표시될 때만 TTS 실행 (가장 최근 봇 응답일 때만 재생)
                    # 여기서는 chat 리스트의 마지막 요소가 현재 순회 중인 메시지와 동일한 경우를 확인
                    if st.session_state["chat"] and st.session_state["chat"][-1] == ("bot", time, message):
                         TTS(message)

if __name__=="__main__":
    main()
