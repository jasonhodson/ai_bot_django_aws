from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import fitz  # PyMuPDF
import openai
import os
import time
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

client = openai.OpenAI()
assistant_id = 'asst_vxGjfP8A2QvmJ3y3FwrgwaX2'

def index(request):
    request.session['file_uploaded'] = False
    return render(request, 'embedded_ai_chatbot/index.html')

def pdf_extract_text(file):
    file_name = file.name.rsplit('.', 1)[0]
    initial_message = f"Here is a credit card statement named `{file_name}`, which was generated from a PDF extract. Please provide me the amount due, number of transactions, and the largest transaction. Please be succinct in all responses unless asked to be more verbose."
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        pdf_text = [initial_message]
        for page in doc:
            pdf_text.append(page.get_text())
        doc.close()
    except Exception as e:
        logger.error(f'Error processing PDF file: {e}')
        return None
    return '\n'.join(pdf_text)

def process_message(request, message):

    if not request.session.get('file_uploaded', False):
        return JsonResponse({'message': 'Please upload a file.'})

    if 'thread_id' not in request.session:
        try:
            thread = client.beta.threads.create()
            request.session['thread_id'] = thread.id
            logging.info(f"New thread created with ID: {thread.id}")
        except Exception as e:
            logger.error(f"Error initializing conversation: {e}")
            return 'Error initializing conversation.'

    try:
        message_response = client.beta.threads.messages.create(
            thread_id=request.session['thread_id'],
            role="user",
            content=message
        )
        run = client.beta.threads.runs.create(
            thread_id=request.session['thread_id'],
            assistant_id=assistant_id
        )

        run_id=run.id

        max_retries = 60
        retry_count = 0
        sleep_interval = 1
        while retry_count < max_retries:
            run_response = client.beta.threads.runs.retrieve(
                thread_id=request.session['thread_id'],
                run_id=run.id
            )

            if run_response.status == 'completed':
                response_messages = client.beta.threads.messages.list(thread_id=request.session['thread_id'])
                logging.info(f"Message response: {response_messages}")

                all_text_content = ""
                for message in response_messages.data:
                    if message.role != 'assistant' or message.run_id != run_id:
                        continue

                    for content in message.content:
                        if content.type == 'text':
                            all_text_content += content.text.value + "\n"
                            logging.info(f"Text Content: {content.text.value}")

                if all_text_content:
                    html_text_content = all_text_content.strip().replace("\n", "<br>")
                    logging.info(f"Message sent to chat window: {html_text_content}")
                    return {'message': html_text_content}
                else:
                    return JsonResponse({'message': 'No response from assistant'})

            time.sleep(sleep_interval)
            retry_count += 1

        return JsonResponse({'message': 'Response taking too long. Please try again later.'})

    except Exception as e:
        logging.error(f'Error processing message: {e}')
        return JsonResponse({'message': f'Error processing message: {e}'})

def chat_with_user(request):
    if request.method == 'POST':
        input_type = request.POST.get('type', 'text')

        if input_type == 'file':
            file = request.FILES.get('file')
            pdf_text = pdf_extract_text(file)
            if pdf_text:
                request.session['file_uploaded'] = True
                response_data = process_message(request, pdf_text)
                return JsonResponse(response_data)
            else:
                return JsonResponse({'message': 'Failed to extract text from PDF.'})

        elif input_type == 'text':
            message = request.POST.get('message', '')
            response_data = process_message(request, message)
            if isinstance(response_data, dict):
                return JsonResponse(response_data)
            else:
                return JsonResponse({'message': response_data})
    else:
        return JsonResponse({'message': 'Invalid request method'})

@csrf_exempt
def delete_files(request):
    request.session.pop('thread_id', None)
    return JsonResponse({'message': 'Session cleared.'})