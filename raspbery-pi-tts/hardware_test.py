#!/usr/bin/env python3
"""
Hardware Test Script for Raspberry Pi TTS System (No GPIO)
Tests all hardware components and dependencies
"""

import sys
import os
import time
import subprocess

def test_python_environment():
    """Test Python environment and version"""
    print("🐍 Testing Python Environment...")
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    
    # Test if we're in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✓ Virtual environment detected")
    else:
        print("⚠️  Not in virtual environment")
    
    return True

def test_audio_system():
    """Test audio system functionality"""
    print("\n🔊 Testing Audio System...")
    
    try:
        # Test ALSA
        result = subprocess.run(['arecord', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✓ ALSA audio system available")
        else:
            print("❌ ALSA not found")
    except:
        print("❌ ALSA test failed")
    
    try:
        # Test audio devices
        result = subprocess.run(['aplay', '-l'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✓ Audio playback devices found")
            # Show first few lines of output
            lines = result.stdout.split('\n')[:3]
            for line in lines:
                if line.strip():
                    print(f"   {line}")
        else:
            print("❌ No audio playback devices")
    except:
        print("❌ Audio device test failed")
    
    return True

def test_espeak():
    """Test espeak installation"""
    print("\n🗣️  Testing espeak...")
    
    try:
        result = subprocess.run(['espeak', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✓ espeak installed")
            version_line = result.stdout.split('\n')[0]
            print(f"   {version_line}")
            
            # Test espeak functionality
            print("   Testing espeak speech...")
            subprocess.run(['espeak', 'Hardware test'], timeout=10)
            print("✓ espeak speech test completed")
            
        else:
            print("❌ espeak not working properly")
            return False
    except subprocess.TimeoutExpired:
        print("❌ espeak test timed out")
        return False
    except Exception as e:
        print(f"❌ espeak test failed: {e}")
        return False
    
    return True

def test_python_packages():
    """Test required Python packages"""
    print("\n📦 Testing Python Packages...")
    
    packages = [
        'pyttsx3',
        'pygame',
        'numpy',
        'psutil',
        'requests'
    ]
    
    all_good = True
    
    for package in packages:
        try:
            __import__(package)
            print(f"✓ {package} imported successfully")
        except ImportError as e:
            print(f"❌ {package} import failed: {e}")
            all_good = False
        except Exception as e:
            print(f"⚠️  {package} import warning: {e}")
    
    return all_good

def test_tts_engines():
    """Test TTS engines"""
    print("\n🎤 Testing TTS Engines...")
    
    # Test pyttsx3
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        
        print(f"✓ pyttsx3 initialized with {len(voices) if voices else 0} voices")
        
        if voices:
            for i, voice in enumerate(voices[:3]):  # Show first 3 voices
                print(f"   Voice {i}: {voice.name}")
        
        # Test speech
        print("   Testing pyttsx3 speech...")
        engine.say("Testing pyttsx3 engine")
        engine.runAndWait()
        print("✓ pyttsx3 speech test completed")
        
        engine.stop()
        
    except Exception as e:
        print(f"❌ pyttsx3 test failed: {e}")
        return False
    
    return True

def test_system_resources():
    """Test system resources"""
    print("\n💻 Testing System Resources...")
    
    try:
        import psutil
        
        # CPU info
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"✓ CPU: {cpu_count} cores, {cpu_percent}% usage")
        
        # Memory info
        memory = psutil.virtual_memory()
        print(f"✓ Memory: {memory.total // 1024 // 1024} MB total, "
              f"{memory.percent}% used")
        
        # Disk info
        disk = psutil.disk_usage('/')
        print(f"✓ Disk: {disk.total // 1024 // 1024 // 1024} GB total, "
              f"{(disk.used / disk.total) * 100:.1f}% used")
        
        # Temperature (Pi specific)
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = int(f.read()) / 1000.0
                print(f"✓ CPU Temperature: {temp}°C")
        except:
            print("⚠️  CPU temperature not available")
        
    except Exception as e:
        print(f"❌ System resource test failed: {e}")
        return False
    
    return True

def test_network():
    """Test network connectivity"""
    print("\n🌐 Testing Network...")
    
    try:
        import requests
        
        # Test internet connectivity
        response = requests.get('https://httpbin.org/ip', timeout=10)
        if response.status_code == 200:
            print("✓ Internet connectivity available")
        else:
            print("⚠️  Internet connectivity issues")
        
    except Exception as e:
        print(f"❌ Network test failed: {e}")
        return False
    
    return True

def run_full_hardware_test():
    """Run complete hardware test suite"""
    print("🧪 RASPBERRY PI TTS HARDWARE TEST")
    print("=" * 50)
    print("Testing all system components and dependencies...")
    print("=" * 50)
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Python Environment", test_python_environment),
        ("Audio System", test_audio_system),
        ("espeak TTS", test_espeak),
        ("Python Packages", test_python_packages),
        ("TTS Engines", test_tts_engines),
        ("System Resources", test_system_resources),
        ("Network", test_network)
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            test_results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            test_results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
    
    print("=" * 50)
    print(f"TOTAL: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System ready for TTS deployment.")
    elif passed >= total * 0.8:
        print("⚠️  Most tests passed. Minor issues detected.")
    else:
        print("❌ Multiple test failures. Check system configuration.")
    
    print("=" * 50)
    
    return passed == total

if __name__ == "__main__":
    success = run_full_hardware_test()
    sys.exit(0 if success else 1)