# NLP-Project
NLP project text
Corso di Natural Language Processing
 
Dear NLP students, please read the following carefully. The text here contains instructions for the project that are mandatory for ALL students. Read up to the end, you all must follow the proposed directives.
 
Step 1:
Implement an autocompleting system for citations based on a graph database containing Wikiquote. Build the Wikiquote graph starting from the official dump
(https://dumps.wikimedia.org/enwikiquote/20250601 (https://dumps.wikimedia.org/enwikiquote/20250601/))/),
create a full-text index on the citations, and autocomplete sentences entered by the user, indicating the source of the best-matching quote identified.
 
Step 2:
 
"Which Quote?" Design and implement an interactive system that allows multiple users to engage vocally with what comes out from Step1 through voice commands, with automatic speaker recognition and the response generation in natural language via a personalized text-to-speech (TTS) synthesizer, configured according to the voice preferences previously associated with the recognized user.
The system should consist of the following modules:
 
• Automatic Speech Recognition (ASR) module: uses pre-trained models to transcribe voice commands. Examples of applicable technologies include Whisper, Wav2Vec2, and NVIDIA NeMo.
 
• Speaker Identification module: based on pre-trained models, such as Titanet from Nemo,
(https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/asr/speaker_recognition/models.html#titanet)
 
it enables both user registration and the creation of voice embeddings for user recognition.
 
Note that fine-tuning the model is not required—it's sufficient to build a database of voice embeddings to distinguish between individual users.
 
• Chatbot module: a conversational interface based on the results of the previous Wikiquote graph project
 
• Personalized Text-to-Speech (TTS) module: uses pre-trained models, such as those
provided by Nvidia Nemo,
 
(https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/tts/models.html (https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/tts/models.html)))
 
to generate vocals in some ways different depending on the voice that uttered the question.
 
For support and clarification concerning Step1, you may contact (only on the teams chat) prof. ANTONIO ORIGLIA
 
For support and clarification concerning Step 2, you may contact (only on the teams chat) prof. VINCENZO NORMAN VITALE
 
The two stesp are mandatory for ALL students, i.e. both DATA-SCIENTISTS and COMPUTER-SCIENTISTS.
 
The project must be undertaken by groups of 2-3 people (singles and fours must be expressly authorized by me). The delivery will consist of code, a short written relation. After the delivery, groups will be called for the presentation of the results through a live demo and a short PPT. 
For Data-scientists the presentation will conclude the exam, Computer-scientists will be asked to answer a couple of questions concerning arguments around Transformers, LLM, RAG LoRA, after the project presentation.
Please do not hesitate to contact me on this chat for any further organizational issues.
