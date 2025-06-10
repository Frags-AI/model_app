from transformers import AutoModelForCausalLM, AutoProcessor  # Florence-2 model interface

class FlorenceModel:
    def __init__(self):
        self.model = AutoModelForCausalLM.from_pretrained(
            "microsoft/Florence-2-large",
            cache_dir="models/florence",
            device_map="cuda",
            trust_remote_code=True,
            torch_dtype='auto'
        ).eval().cuda()

        self.processor = AutoProcessor.from_pretrained(
            "microsoft/Florence-2-large",
            cache_dir="models/florence",
            trust_remote_code=True
        )

    def get_details(self):
        return (self.model, self.processor)
    
    def destroy(self):
        del self.model
        del self.processor
    
def load_florence_model():
    return FlorenceModel()