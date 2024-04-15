"""Main file for the Amatsuki project"""
import os
from os import PathLike
from time import time
import asyncio
from typing import Union

from dotenv import load_dotenv
import openai
from deepgram import Deepgram
import pygame
from pygame import mixer
import elevenlabs

from record import speech_to_text

# Load API keys
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
elevenlabs.set_api_key(os.getenv("ELEVENLABS_API_KEY"))

# Initialize APIs
gpt_client = openai.Client(api_key=OPENAI_API_KEY)
deepgram = Deepgram(DEEPGRAM_API_KEY)
# mixer is a pygame module for playing audio
mixer.init()

# Change the context if you want to change Amatsuki' personality

conversation = {"Conversation": []}
RECORDING_PATH = "audio/recording.wav"


def request_gpt(prompt: str) -> str:
    """
    GPT-4 APIにプロンプトを送信し、応答を日本語で受け取ります。

    Args:
        prompt (str): GPT-4 APIに送信するプロンプト(日本語)

    Returns:
        str: GPT-4からの応答(日本語)
    """
    response = gpt_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": 
                """
                あなたはChatbotとして、天然で可愛げのある男の子、アマツキのロールプレイを行います。
                以下の制約条件を厳密に守ってロールプレイを行ってください。

                制約条件:
                * Chatbotの自身を示す一人称は、僕です。
                * Userを示す二人称は、君です。
                * Chatbotの名前は、アマツキです。
                * 変な日本語は話しません。
                * アマツキは爽やかで甘い少年ボイスで明るく真っすぐな人柄です。
                * ユーザーと日常会話を話して下さい。
                * フレンドリーな口調で親しみやすいキャラクターとして振る舞って下さい。
                * 話すときはタメ口でUserに会話の最後に話してた内容に関連する質問をして下さい。
                # 会話例
                User: おはよう
                アマツキ: おはよう!！今日は何か予定ある？
                User: 今日は遊びに行く予定だよ
                アマツキ: へぇ〜！いいね！どこに遊び行くの？
                User: 友達と有名なラーメン屋さん行く！
                アマツキ:僕もラーメン好きだよ! 因みにどこのラーメン屋さんなの？

                # アマツキのプロフィール
                あだ名: あまちゅ
                血液型: A型
                身長: 176cm
                誕生日: 1991年6月30日
                出身・在住: 東京都
                口癖: お腹すいた、イケメン爆発しろ
                趣味: 漫画、ゲーム、アニメ、映画鑑賞、写真撮影
                好き: 歌、エルモ、焼肉、プリン、コーラ、平沢唯、etc… 

                # アマツキの行動指針:
                * ユーザーにやさしく接してください。
                * ユーザーを励ましてください。
                * セクシャルな話題については適切に避けてください。

                """
            },
            {
                "role": "user",
                "content": f"{prompt}",
            }
        ],
        model="gpt-4",
        temperature=0.7,  # 応答の多様性を調整
    )
    return response.choices[0].message.content


async def transcribe(
    file_name: Union[Union[str, bytes, PathLike[str], PathLike[bytes]], int]
):
    """
    Transcribe audio using Deepgram API.

    Args:
        - file_name: The name of the file to transcribe.

    Returns:
        The response from the API.
    """
    with open(file_name, "rb") as audio:
        source = {"buffer": audio, "mimetype": "audio/wav"}
        options = {"language": "ja","model":"nova-2-general",}
        response = await deepgram.transcription.prerecorded(source, options)
        return response["results"]["channels"][0]["alternatives"][0]["words"]


def log(log: str):
    """
    Print and write to status.txt
    """
    print(log)
    with open("status.txt", "w") as f:
        f.write(log)


if __name__ == "__main__":
    while True:
        # Record audio
        log("Listening...")
        speech_to_text()
        log("Done listening")

        # Transcribe audio
        current_time = time()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        words = loop.run_until_complete(transcribe(RECORDING_PATH))
        string_words = " ".join(
            word_dict.get("word") for word_dict in words if "word" in word_dict
        )
        with open("conv.txt", "a") as f:
            f.write(f"{string_words}\n")
        transcription_time = time() - current_time
        log(f"Finished transcribing in {transcription_time:.2f} seconds.")

            # Get response from GPT-3
        current_time = time()
        response = request_gpt(string_words)  # ユーザーの入力を直接引数として渡す
        gpt_time = time() - current_time
        log(f"Finished generating response in {gpt_time:.2f} seconds.")

        # Convert response to audio
        current_time = time()
        audio = elevenlabs.generate(
            text=response, voice="天月", model="eleven_multilingual_v2"
        )
        elevenlabs.save(audio, "audio/response.wav")
        audio_time = time() - current_time
        log(f"Finished generating audio in {audio_time:.2f} seconds.")

        # Play response
        log("Speaking...")
        sound = mixer.Sound("audio/response.wav")
        # Add response as a new line to conv.txt
        with open("conv.txt", "a") as f:
            f.write(f"{response}\n")
        sound.play()
        pygame.time.wait(int(sound.get_length() * 1000))
        print(f"\n --- USER: {string_words}\n --- Amatuki: {response}\n")