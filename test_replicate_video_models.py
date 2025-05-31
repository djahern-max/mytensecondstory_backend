import replicate
import os
from dotenv import load_dotenv

load_dotenv()
client = replicate.Client(api_token=os.getenv('REPLICATE_API_TOKEN'))

print("🧪 TESTING DIFFERENT REPLICATE VIDEO BACKGROUND REMOVAL MODELS")
print("=" * 60)

# List of video background removal models to test
video_models = [
    {
        "name": "lucataco/rembg-video",
        "version": "c18392381d1b5410b5a76b9b0c58db132526d3f79fe602e04e0d80cb668df509",
        "params": {
            "mode": "Fast",
            "video": "MyIntro_Test.mp4",
            "background_color": "#000000"
        }
    },
    {
        "name": "arielreplicate/robust_video_matting", 
        "version": "73d2128a371922d5d1abf0712a1d974be0e4e2358cc1218e4e34714767232bac",
        "params": {
            "input_video": "MyIntro_Test.mp4",
            "output_type": "green-screen"
        }
    },
    {
        "name": "arielreplicate/robust_video_matting",
        "version": "73d2128a371922d5d1abf0712a1d974be0e4e2358cc1218e4e34714767232bac", 
        "params": {
            "input_video": "MyIntro_Test.mp4",
            "output_type": "alpha-mask"
        }
    },
    {
        "name": "nateraw/video-background-remover",
        "version": None,  # Try without version first
        "params": {
            "video": "MyIntro_Test.mp4"
        }
    }
]

for i, model in enumerate(video_models):
    print(f"\n🧪 TEST {i+1}: {model['name']}")
    print(f"   Version: {model['version']}")
    print(f"   Params: {list(model['params'].keys())}")
    
    try:
        # Build model string
        model_string = model['name']
        if model['version']:
            model_string += f":{model['version']}"
        
        # Prepare input - open file for video parameter
        input_params = {}
        for key, value in model['params'].items():
            if 'video' in key.lower():
                input_params[key] = open(value, "rb")
            else:
                input_params[key] = value
        
        print(f"   🚀 Running {model_string}...")
        
        output = client.run(
            model_string,
            input=input_params,
            use_file_output=False
        )
        
        print(f"   ✅ SUCCESS!")
        print(f"   📤 Output: {output}")
        print(f"   📁 File type: {type(output)}")
        
        # Check if it's a video URL
        if isinstance(output, str):
            if '.mp4' in output.lower() or '.mov' in output.lower():
                print(f"   🎬 VIDEO DETECTED! This model works!")
            elif '.png' in output.lower() or '.jpg' in output.lower():
                print(f"   🖼️  Image detected - not a video")
            else:
                print(f"   ❓ Unknown file type")
        else:
            print(f"   ❓ Non-string output: {output}")
            
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        
    print("-" * 40)

print("\n🏁 TEST COMPLETE!")
print("Look for models marked with '🎬 VIDEO DETECTED!' - those are the working ones!")
