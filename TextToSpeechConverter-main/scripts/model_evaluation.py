# model_evaluation.py

import time
import os
import pyttsx3
from gtts import gTTS
import matplotlib.pyplot as plt
import psutil
import numpy as np
import platform
import json
import shutil
from datetime import datetime

# Define paths relative to the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
MODELS_DIR = os.path.join(PROJECT_DIR, 'models')
SAMPLES_DIR = os.path.join(PROJECT_DIR, 'samples')
DOCS_DIR = os.path.join(PROJECT_DIR, 'docs')

# Ensure directories exist
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(SAMPLES_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

def measure_performance(model_name, tts_function, text):
    # Start measuring
    start_time = time.time()
    start_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # in MB
    cpu_percent = psutil.cpu_percent(interval=None)
    
    # Run TTS function
    tts_function(text)
    
    # Measure after execution
    end_time = time.time()
    end_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # in MB
    
    # Calculate metrics
    elapsed_time = end_time - start_time
    memory_used = end_memory - start_memory
    cpu_used = psutil.cpu_percent(interval=None) - cpu_percent
    
    # Return performance metrics
    return {
        'model': model_name,
        'time': elapsed_time,
        'memory': memory_used,
        'cpu': cpu_used
    }

def pyttsx3_tts(text, output_path=None):
    """TTS using pyttsx3 (offline, SAPI5 on Windows)"""
    engine = pyttsx3.init()
    
    if output_path:
        # When saving to a specific output file
        try:
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            print(f"  Audio saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"  Warning: Error saving to {output_path}: {e}")
            # Try an alternative approach
            engine.say(text)
            engine.runAndWait()
            return None
    else:
        # When just playing audio without saving
        engine.say(text)
        engine.runAndWait()
        
        # Calculate appropriate wait time based on text length
        # Assuming average speaking rate of 150 words per minute (2.5 words per second)
        words = len(text.split())
        wait_time = max(3, words / 2.5)  # At least 3 seconds
        time.sleep(min(wait_time, 10))  # Cap at 10 seconds max wait
        
        return None

def gtts_tts(text, output_path=None):
    """TTS using Google Text-to-Speech (online)"""
    if output_path:
        path = output_path
    else:
        # Use fixed filenames based on text type
        if len(text) < 50:  # Arbitrary threshold for short text
            path = os.path.join(SAMPLES_DIR, "gtts_short.mp3")
        elif len(text) < 200:  # Arbitrary threshold for medium text
            path = os.path.join(SAMPLES_DIR, "gtts_medium.mp3")
        else:  # Long text
            path = os.path.join(SAMPLES_DIR, "gtts_long.mp3")
    
    # Generate speech
    tts = gTTS(text=text, lang='en', slow=False)
    
    try:
        # Try to save to the file
        tts.save(path)
        print(f"  Audio saved to {path}")
    except PermissionError:
        # If permission error (file in use), use a unique name
        unique_path = os.path.join(SAMPLES_DIR, f"gtts_{int(time.time())}.mp3")
        print(f"  Cannot access {path}, using {unique_path} instead")
        tts.save(unique_path)
        path = unique_path
    
    # Play the file if not saving to a specific path
    if not output_path:
        # Fix for Windows paths with spaces
        os.system(f'start "" "{path}"')
        
        # Calculate appropriate wait time based on text length
        # Assuming average speaking rate of 150 words per minute (2.5 words per second)
        words = len(text.split())
        wait_time = max(3, words / 2.5)  # At least 3 seconds
        time.sleep(min(wait_time, 10))  # Cap at 10 seconds max wait
    
    return path

def compare_models():
    """Compare different TTS models and visualize results"""
    # Test text samples of varying length
    short_text = "Welcome to the Text-to-Speech demo."
    medium_text = "This is a demonstration of Text-to-Speech technology using different models. We are comparing their performance and quality."
    long_text = "Text-to-Speech technology is evolving rapidly with many options available. Some models run completely offline, while others require internet connectivity. Factors to consider include speech quality, latency, resource usage, and deployment requirements. This project evaluates these factors to find the best option for a Raspberry Pi implementation."
    
    test_text = medium_text  # Use medium text for testing
    
    # Define models to test
    models = [
        {"name": "pyttsx3 (Offline)", "function": pyttsx3_tts, "type": "Offline", "size": "Small (2-5MB)"},
        {"name": "Google TTS (Online)", "function": gtts_tts, "type": "Online", "size": "Cloud-based"}
    ]
    
    # Run performance tests
    results = []
    print("Running performance tests...")
    
    for model in models:
        print(f"\nTesting {model['name']}...")
        # Generate permanent sample with model name
        sample_path = os.path.join(SAMPLES_DIR, f"{model['name'].replace(' ', '_').lower()}.mp3")
        model['function'](test_text, sample_path)
        print(f"  Sample saved to: {sample_path}")
        
        # Measure performance with short text
        print("  Measuring performance with short text...")
        short_result = measure_performance(f"{model['name']} (Short)", 
                                   lambda t: model['function'](t, None), 
                                   short_text)
        results.append(short_result)
        
        # Measure performance with medium text
        print("  Measuring performance with medium text...")
        medium_result = measure_performance(f"{model['name']} (Medium)", 
                                   lambda t: model['function'](t, None), 
                                   medium_text)
        results.append(medium_result)
        
        # Measure performance with long text
        print("  Measuring performance with long text...")
        long_result = measure_performance(f"{model['name']} (Long)", 
                                   lambda t: model['function'](t, None), 
                                   long_text)
        results.append(long_result)
        
        # Print summary
        print(f"  Time (Medium text): {medium_result['time']:.2f}s")
        print(f"  Memory usage: {medium_result['memory']:.2f} MB")
        print(f"  CPU usage: {medium_result['cpu']:.2f}%")
    
    # Create comparison visualizations
    create_visualizations(results, models)
    
    # Save results
    save_results(results, models)
    
    # Return results and models
    return results, models
           
def create_visualizations(results, models):
    """Create visualization of performance metrics"""
    print("\nGenerating visualizations...")
    
    # Filter results for medium text only for cleaner charts
    medium_results = [r for r in results if "(Medium)" in r['model']]
    
    # Extract model names without the "(Medium)" suffix
    model_names = [r['model'].replace(" (Medium)", "") for r in medium_results]
    
    # Extract metrics
    times = [r['time'] for r in medium_results]
    memory = [r['memory'] for r in medium_results]
    cpu = [r['cpu'] for r in medium_results]
    
    # Create figure with subplots
    fig, axs = plt.subplots(3, 1, figsize=(10, 12))
    
    # Plot processing time
    axs[0].bar(model_names, times, color='blue')
    axs[0].set_title('Processing Time (seconds)')
    axs[0].set_ylabel('Time (s)')
    axs[0].grid(axis='y', linestyle='--', alpha=0.7)
    
    # Plot memory usage
    axs[1].bar(model_names, memory, color='green')
    axs[1].set_title('Memory Usage (MB)')
    axs[1].set_ylabel('Memory (MB)')
    axs[1].grid(axis='y', linestyle='--', alpha=0.7)
    
    # Plot CPU usage
    axs[2].bar(model_names, cpu, color='red')
    axs[2].set_title('CPU Usage (%)')
    axs[2].set_ylabel('CPU (%)')
    axs[2].grid(axis='y', linestyle='--', alpha=0.7)
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(os.path.join(DOCS_DIR, 'model_comparison.png'))
    print(f"  Visualization saved to {os.path.join(DOCS_DIR, 'model_comparison.png')}")
    plt.close()

def save_results(results, models):
    """Save test results to file"""
    # Create summary for documentation
    summary = {
        "test_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "system": {
            "os": platform.system() + " " + platform.version(),
            "processor": platform.processor(),
            "python": platform.python_version()
        },
        "models": [
            {
                "name": model["name"],
                "type": model["type"],
                "size": model["size"]
            } for model in models
        ],
        "results": results
    }
    
    # Save as JSON
    with open(os.path.join(DOCS_DIR, 'model_test_results.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Create markdown report
    with open(os.path.join(DOCS_DIR, 'phase2_model_selection.md'), 'w') as f:
        f.write("# Phase 2: Model Selection & Optimization\n\n")
        f.write(f"**Test Date:** {summary['test_date']}\n\n")
        
        f.write("## System Information\n")
        f.write(f"- **OS:** {summary['system']['os']}\n")
        f.write(f"- **Processor:** {summary['system']['processor']}\n")
        f.write(f"- **Python:** {summary['system']['python']}\n\n")
        
        f.write("## Models Evaluated\n\n")
        f.write("| Model | Type | Size | Processing Time (s) | Memory Usage (MB) | CPU Usage (%) |\n")
        f.write("|-------|------|------|---------------------|-------------------|---------------|\n")
        
        # Filter for medium text results
        medium_results = [r for r in results if "(Medium)" in r['model']]
        
        for i, model in enumerate(models):
            r = medium_results[i]
            model_name = model["name"]
            model_type = model["type"]
            model_size = model["size"]
            time_val = f"{r['time']:.2f}"
            memory_val = f"{r['memory']:.2f}"
            cpu_val = f"{r['cpu']:.2f}"
            
            f.write(f"| {model_name} | {model_type} | {model_size} | {time_val} | {memory_val} | {cpu_val} |\n")
        
        f.write("\n## Performance Comparison\n\n")
        f.write("![Model Comparison](model_comparison.png)\n\n")
        
        f.write("## Optimization for Raspberry Pi\n\n")
        f.write("Based on the performance analysis, the following optimizations are recommended for Raspberry Pi deployment:\n\n")
        
        # Determine best model for Pi based on resource usage
        best_model = min(medium_results, key=lambda x: x['time'] + x['memory']/10)
        best_model_name = best_model['model'].replace(" (Medium)", "")
        
        f.write(f"1. **Selected Model:** {best_model_name}\n")
        if "pyttsx3" in best_model_name:
            f.write("   - **Rationale:** Fully offline, low resource usage, suitable for Raspberry Pi's limited resources\n")
            f.write("   - **Implementation:** Direct integration with minimal modifications\n\n")
        elif "Google" in best_model_name:
            f.write("   - **Rationale:** Superior voice quality with acceptable performance\n")
            f.write("   - **Implementation:** Requires internet connectivity, caching for frequently used phrases recommended\n\n")
        
        f.write("2. **Resource Optimization:**\n")
        f.write("   - Implement text preprocessing to remove unnecessary content\n")
        f.write("   - Cache frequently used phrases\n")
        f.write("   - Implement resource monitoring and throttling if CPU usage exceeds thresholds\n\n")
        
        f.write("3. **Performance Considerations:**\n")
        f.write("   - Raspberry Pi's limited CPU will increase processing time compared to laptop testing\n")
        f.write("   - Memory usage should remain consistent\n")
        f.write("   - For longer texts, consider implementing chunking to process text in manageable segments\n\n")
        
        f.write("## Next Steps\n\n")
        f.write("- Implement the selected model with optimizations\n")
        f.write("- Develop the user interface (CLI or simple GUI)\n")
        f.write("- Create error handling for edge cases\n")
    
    print(f"  Results saved to {os.path.join(DOCS_DIR, 'model_test_results.json')}")
    print(f"  Report saved to {os.path.join(DOCS_DIR, 'phase2_model_selection.md')}")

if __name__ == "__main__":
    # Install required packages if not already installed
    try:
        import gtts
    except ImportError:
        print("Installing gTTS package...")
        os.system("pip install gtts")
        from gtts import gTTS
    
    try:
        import psutil
    except ImportError:
        print("Installing psutil package...")
        os.system("pip install psutil")
        import psutil
    
    print("Starting TTS Model Evaluation...")
    results, models = compare_models()
    print("\nModel evaluation complete!")


    