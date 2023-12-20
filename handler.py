import runpod
import os
import time
import whisperx
import gc 
import base64
import tempfile

# CHECK THE ENV VARIABLES FOR DEVICE AND COMPUTE TYPE
device = os.environ.get('DEVICE', 'cuda') # cpu if on Mac
compute_type = os.environ.get('COMPUTE_TYPE', 'float16') #int8 if on Mac
batch_size = 16 # reduce if low on GPU mem
language_code = "en"

def base64_to_tempfile(base64_data):
    """
    Decode base64 data and write it to a temporary file.
    Returns the path to the temporary file.
    """
    # Decode the base64 data to bytes
    audio_data = base64.b64decode(base64_data)

    # Create a temporary file and write the decoded data
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    with open(temp_file.name, 'wb') as file:
        file.write(audio_data)

    return temp_file.name

def handler(event):
    '''
    Run inference on the model.
    Returns output path, width the seed used to generate the image.
    '''
    job_input = event['input']
    job_input_audio_base_64 = job_input['audio_base_64']
    if(job_input_audio_base_64 is None):
        raise Exception("audio_base_64 is required")
    audio_input = base64_to_tempfile(job_input_audio_base_64)

    # 1. Transcribe with original whisper (batched)
    model = whisperx.load_model("small", device, compute_type=compute_type, language="en")

    # Load the audio
    audio = whisperx.load_audio(audio_input)
    # Transcribe the audio
    result = model.transcribe(audio, batch_size=batch_size, language=language_code, print_progress=True)

    # 2. Align whisper output
    model_a, metadata = whisperx.load_align_model(language_code=language_code, device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio, device)
    print(result["segments"]) # after alignment


    return result

runpod.serverless.start({
    "handler": handler
})
