from shortGPT.gpt import gpt_utils
import random
import json
import re

def generateRedditPostMetadata(title):
    name = generateUsername()
    if title and title[0] == '"':
        title = title.replace('"', '')
    n_months = random.randint(1,11)
    header = f"{name} - {n_months} months ago"
    n_comments = random.random() * 10 + 2
    n_upvotes = n_comments*(1.2+ random.random()*2.5)
    return title, header, f"{n_comments:.1f}k", f"{n_upvotes:.1f}k"


def getInterestingRedditQuestion(subreddit="AskReddit", previously_used=[]):
    chat, system = gpt_utils.load_local_yaml_prompt('prompt_templates/reddit_generate_question.yaml')
    chat = chat.replace("<<SUBREDDIT>>", subreddit)
    
    previous_str = "\n".join([f"- {q}" for q in previously_used])
    chat = chat.replace("<<PREVIOUSLY_USED>>", previous_str)
    
    return gpt_utils.llm_completion(chat_prompt=chat, system=system, temp=1.08)

def createRedditScript(question, mode="default", previous_scripts=[]):
    chat, system = gpt_utils.load_local_yaml_prompt('prompt_templates/reddit_generate_script.yaml')
    chat = chat.replace("<<QUESTION>>", question)
    
    # Add previous scripts to avoid
    prev_str = "\n".join([f"- {s[:50]}..." for s in previous_scripts])
    chat = chat.replace("<<PREVIOUS_SCRIPTS>>", prev_str)
    
    if mode == "cringe":
        system += " The story should be embarrassing, awkward, and cringe-worthy. Focus on social mishaps."
    elif mode == "glitch":
        system += " The story should be mysterious, unsettling, and inexplicable. Focus on glitches in reality."
    elif mode == "revenge":
        system += " The story should be satisfying, petty, and vindictive. Focus on getting back at someone."
    elif mode == "nostalgia_horror":
        system += " The story should be a dark, twisted fact or urban legend about a 90s/00s childhood toy or trend."
    elif mode == "biological_horror":
        system += " The story should be visceral, disturbing, and focused on parasites, diseases, or body horror. Start with a hook like 'You won't believe what lives inside...'."
    elif mode == "cosmic_dread":
        system += " The story should be existential, vast, and terrifying. Focus on the void, black holes, or the end of the universe."
    elif mode == "hidden_history":
        system += " The story should be a fast-paced, energetic 'Did you know' fact about history or artifacts."
    elif mode == "simulation_glitch":
        system += " The story should combine a user story about a glitch with a scientific explanation (Quantum physics, Mandela Effect). Make reality feel fake."

    result = "Reddit, " + question +" "+gpt_utils.llm_completion(chat_prompt=chat, system=system, temp=1.08)
    return result
    

def getRealisticness(text):
    chat, system = gpt_utils.load_local_yaml_prompt('prompt_templates/reddit_filter_realistic.yaml')
    chat = chat.replace("<<INPUT>>", text)
    attempts = 0
    while attempts <= 4:
        attempts+=1
        try:
            result = gpt_utils.llm_completion(chat_prompt=chat, system=system, temp=1)
            # Clean up result to handle markdown code blocks
            cleaned_result = result.strip()
            if "```" in cleaned_result:
                match = re.search(r"```(?:json)?(.*?)```", cleaned_result, re.DOTALL)
                if match:
                    cleaned_result = match.group(1).strip()
            
            # Try to find JSON object if there's extra text
            match = re.search(r"\{.*\}", cleaned_result, re.DOTALL)
            if match:
                cleaned_result = match.group(0)
                
            return json.loads(cleaned_result)['score']
        except Exception as e:
            print(f"Error in getRealisticness: {e}")
            print(f"Failed result content: {result}")
    raise Exception("LLM Failed to generate a realisticness score on the script")

def getQuestionFromThread(text):
    if ((text.find("Reddit, ") < 15) and (10 < text.find("?") < 100)):
        question = text.split("?")[0].replace("Reddit, ", "").strip().capitalize()
    else:
        chat, system = gpt_utils.load_local_yaml_prompt('prompt_templates/reddit_filter_realistic.yaml')
        chat = chat.replace("<<STORY>>", text)
        question = gpt_utils.llm_completion(chat_prompt=chat, system=system).replace("\n", "")
        question = question.replace('"', '').replace("?", "")
    return question


def generateUsername():
    chat, system = gpt_utils.load_local_yaml_prompt('prompt_templates/reddit_username.yaml')
    return gpt_utils.llm_completion(chat_prompt=chat, system=system, temp=1.2).replace("u/", "")


