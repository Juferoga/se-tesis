from ollama import chat
from ollama import ChatResponse

def descomprimir(mensaje_comprimido):
  #print("\n:::::MENSAJE:::::\n", mensaje_comprimido)

  prompt_reconstruccion = (
    "You are reconstructing a text that was lossy-compressed and may contain garbled or missing tokens.\n"
    "Task: produce the most faithful readable reconstruction of the original message.\n"
    "Rules:\n"
    "1) Preserve original meaning, chronology, and details.\n"
    "2) Do not add new facts, names, places, numbers, or events.\n"
    "3) Keep the same language as the input.\n"
    "4) If a fragment is ambiguous, choose the safest wording that changes the meaning the least.\n"
    "5) Return only the reconstructed text, with no notes or explanations.\n"
    "Compressed input:\n"
    "<<<\n"
    f"{mensaje_comprimido}\n"
    ">>>"
  )

  response: ChatResponse = chat(
    model='gemma3:4b',
    messages=[
      {
        'role': 'user',
        'content': prompt_reconstruccion,
      },
    ]
  )

  #print("::::RESPUESTA::::\n",response['message']['content'])
  return response['message']['content']
