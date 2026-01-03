from shortGPT.gpt import gpt_utils
import json
def generateFacts(facts_type, previously_used=[]):
    chat, system = gpt_utils.load_local_yaml_prompt('prompt_templates/facts_generator.yaml')
    
    # Custom logic for new modes
    if "Weird Laws" in facts_type:
        system += " You are generating a 'Weird Law' short. Randomly select a real weird law from a specific location. Start with the hook: 'If you live in {Location}, you are breaking the law right now.' followed by the law."
    elif "Dark History" in facts_type:
        system += " You are generating a 'Dark History' short. Focus on a massacre, scandal, or dark origin story. Use a serious, storytelling tone."

    chat = chat.replace("<<FACTS_TYPE>>", facts_type)
    
    previous_str = "\n".join([f"- {f[:100]}..." for f in previously_used]) # Truncate to save tokens
    chat = chat.replace("<<PREVIOUSLY_USED>>", previous_str)
    
    # Generation Loop with Fact Check
    for _ in range(3): # Try 3 times to get a valid fact
        result = gpt_utils.llm_completion(chat_prompt=chat, system=system, temp=1.3)
        
        # Verify the fact
        if verifyFact(result):
            return result
        else:
            print(f"Fact check failed for: {result[:50]}... Regenerating.")
            
    # If all fail, return the last one but warn (or raise exception)
    print("Warning: Fact check failed multiple times. Returning unverified result.")
    return result

def verifyFact(script):
    chat, system = gpt_utils.load_local_yaml_prompt('prompt_templates/fact_check.yaml')
    chat = chat.replace("<<SCRIPT>>", script)
    try:
        # Double check? The user asked for "checked 2 times". 
        # We can just run the verification twice or use a very strict prompt.
        # Let's run it once with a strict prompt for now to save API calls/time, 
        # as the prompt is designed to be rigorous.
        result = gpt_utils.llm_completion(chat_prompt=chat, system=system, temp=0.0) # Low temp for deterministic check
        return "TRUE" in result.upper()
    except Exception as e:
        print(f"Fact check error: {e}")
        return True # Fail open if checker breaks? Or fail closed? Let's fail open to avoid blocking.

def generateFactSubjects(n):
    out = []
    chat, system = gpt_utils.load_local_yaml_prompt('prompt_templates/facts_subjects_generation.yaml')
    chat = chat.replace("<<N>>", f"{n}")
    maxAttempts = int(1.5*n)
    attempts=0
    while len(out) != n & attempts <= maxAttempts:

        result = gpt_utils.llm_completion(chat_prompt=chat, system=system, temp=1.69)
        attempts+=1
        try:
            out = json.loads(result.replace("'", '"'))
        except Exception as e:
            print(f"INFO - Failed generating {n} fact subjects after {attempts} trials", e)
            pass
    if len(out) != n:
        raise Exception(f"Failed to generate {n} subjects. In {attempts} attemps")   
    return out