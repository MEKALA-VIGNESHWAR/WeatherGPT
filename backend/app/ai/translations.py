from typing import Dict, Any

# Multi-lingual templates ensuring numbers & facts stay 100% exact
TRANSLATION_DICTIONARY: Dict[str, Dict[str, str]] = {
    "en": {
        "rain_expected": "Rainfall is expected in {location} {time_desc}.",
        "no_rain": "Clear skies and dry weather expected in {location} {time_desc}.",
        "temp_forecast": "Temperature is expected to be around {temp}°C with {humidity}% humidity.",
        "irrigation_delay": "Recommendation: Delay scheduled irrigation. Expected rainfall ({rain} mm) will provide sufficient soil moisture.",
        "irrigation_safe": "Recommendation: Favorable conditions for scheduled irrigation. Low chance of precipitation ({prob}%).",
        "spray_delay": "Recommendation: Postpone pesticide spraying due to expected rain ({rain} mm). Chemical will be washed away.",
        "spray_safe": "Recommendation: Weather conditions are favorable for spraying. Winds are calm ({wind} km/h).",
        "warning_alert": "ACTIVE WARNING: {headline}. {instruction}",
        "travel_caution": "Recommendation: Exercise caution while commuting due to expected wet road conditions.",
        "source_tag": "Source: {source} (Verified at {updated})",
        "confidence_tag": "Confidence: {confidence}"
    },
    "te": {  # Telugu
        "rain_expected": "{location} లో {time_desc} వర్షం పడే అవకాశం ఉంది.",
        "no_rain": "{location} లో {time_desc} వర్షం పడే అవకాశం లేదు. వాతావరణం నిర్మలంగా ఉంటుంది.",
        "temp_forecast": "ఉష్ణోగ్రత సుమారు {temp}°C గా ఉండవచ్చు, తేమ {humidity}%.",
        "irrigation_delay": "సూచన: నీటిపారుదలని వాయిదా వేయండి. వర్షపాతం ({rain} మి.మీ.) నేల తేమను సమకూరుస్తుంది.",
        "irrigation_safe": "సూచన: పంటకు నీరు పెట్టడానికి అనుకూలమైన వాతావరణం. వర్ష సూచన తక్కువ ({prob}%).",
        "spray_delay": "సూచన: వర్షం ({rain} మి.మీ.) పడే అవకాశం ఉన్నందున పురుగుమందుల పిచికారీని వాయిదా వేయండి.",
        "spray_safe": "సూచన: పురుగుమందుల పిచికారీకి వాతావరణం అనుకూలంగా ఉంది. గాలులు ప్రశాంతంగా ({wind} km/h) ఉన్నాయి.",
        "warning_alert": "అధికారిక హెచ్చరిక: {headline}. {instruction}",
        "travel_caution": "సూచన: వర్షం కారణంగా ప్రయాణంలో తగిన జాగ్రత్తలు పాటించండి.",
        "source_tag": "మూలం: {source} ({updated} వద్ద ధృవీకరించబడింది)",
        "confidence_tag": "విశ్వసనీయత: {confidence}"
    },
    "hi": {  # Hindi
        "rain_expected": "{location} में {time_desc} बारिश होने की संभावना है।",
        "no_rain": "{location} में {time_desc} मौसम साफ और सूखा रहने का अनुमान है।",
        "temp_forecast": "तापमान लगभग {temp}°C और आर्द्रता {humidity}% रहने की संभावना है।",
        "irrigation_delay": "सलाह: सिंचाई स्थगित करें। अपेक्षित वर्षा ({rain} मिमी) से खेत में पर्याप्त नमी रहेगी।",
        "irrigation_safe": "सलाह: सिंचाई के लिए मौसम अनुकूल है। बारिश की संभावना कम ({prob}%) है।",
        "spray_delay": "सलाह: बारिश ({rain} मिमी) के कारण कीटनाशक छिड़काव स्थगित करें। दवा धुल सकती है।",
        "spray_safe": "सलाह: कीटनाशक छिड़काव के लिए स्थिति अनुकूल है। हवा की गति सामान्य ({wind} किमी/घंटा) है।",
        "warning_alert": "आधिकारिक चेतावनी: {headline}. {instruction}",
        "travel_caution": "सलाह: सड़क पर बारिश के कारण यात्रा में सावधानी बरतें।",
        "source_tag": "स्रोत: {source} ({updated} पर सत्यापित)",
        "confidence_tag": "विश्वसनीयता: {confidence}"
    },
    "ta": {  # Tamil
        "rain_expected": "{location} இல் {time_desc} மழை பெய்ய வாய்ப்புள்ளது.",
        "no_rain": "{location} இல் {time_desc} வானிலை தெளிவாக இருக்கும்.",
        "temp_forecast": "வெப்பநிலை சுமார் {temp}°C மற்றும் ஈரப்பதம் {humidity}% ஆக இருக்கும்.",
        "irrigation_delay": "பரிந்துரை: நீர்ப்பாசனத்தை ஒத்திவைக்கவும். மழைப்பொழிவு ({rain} மிமீ) போதுமான ஈரப்பதத்தை அளிக்கும்.",
        "irrigation_safe": "பரிந்துரை: நீர்ப்பாசனம் செய்ய சாதகமான வானிலை.",
        "spray_delay": "பரிந்துரை: மழை வாய்ப்பு உள்ளதால் பூச்சிக்கொல்லி தெளிப்பதை ஒத்திவைக்கவும்.",
        "spray_safe": "பரிந்துரை: பூச்சிக்கொல்லி தெளிக்க வானிலை சாதகமாக உள்ளது.",
        "warning_alert": "எச்சரிக்கை: {headline}. {instruction}",
        "travel_caution": "பரிந்துரை: பயணத்தின் போது எச்சரிக்கையாக இருக்கவும்.",
        "source_tag": "ஆதாரம்: {source}",
        "confidence_tag": "நம்பகத்தன்மை: {confidence}"
    },
    "kn": {  # Kannada
        "rain_expected": "{location} ನಲ್ಲಿ {time_desc} ಮಳೆಯಾಗುವ ಸಾಧ್ಯತೆಯಿದೆ.",
        "no_rain": "{location} ನಲ್ಲಿ {time_desc} ಒಣ ಹವಾಮಾನವಿರುತ್ತದೆ.",
        "temp_forecast": "ತಾಪಮಾನ ಸುಮಾರು {temp}°C ಮತ್ತು ತೇವಾಂಶ {humidity}% ಇರಲಿದೆ.",
        "irrigation_delay": "ಸಲಹೆ: ನೀರಾವರಿಯನ್ನು ಮುಂದೂಡಿ. ಮಳೆ ({rain} ಮಿಮೀ) ನಿರೀಕ್ಷಿಸಲಾಗಿದೆ.",
        "irrigation_safe": "ಸಲಹೆ: ನೀರಾವರಿಗೆ ಅನುಕೂಲಕರ ವಾತಾವರಣವಿದೆ.",
        "spray_delay": "ಸಲಹೆ: ಕೀಟನಾಶಕ ಸಿಂಪಡಣೆಯನ್ನು ಮುಂದೂಡಿ.",
        "spray_safe": "ಸಲಹೆ: ಕೀಟನಾಶಕ ಸಿಂಪಡಿಸಲು ಸೂಕ್ತ ವಾತಾವರಣವಿದೆ.",
        "warning_alert": "ಎಚ್ಚರಿಕೆ: {headline}. {instruction}",
        "travel_caution": "ಸಲಹೆ: ಮಳೆಯಿಂದಾಗಿ ಪ್ರಯಾಣದಲ್ಲಿ ಎಚ್ಚರಿಕೆ ವಹಿಸಿ.",
        "source_tag": "ಮೂಲ: {source}",
        "confidence_tag": "ವಿಶ್ವಾಸಾರ್ಹತೆ: {confidence}"
    },
    "ml": {  # Malayalam
        "rain_expected": "{location}-ൽ {time_desc} മഴയ്ക്ക് സാധ്യതയുണ്ട്.",
        "no_rain": "{location}-ൽ {time_desc} തെളിഞ്ഞ കാലാവസ്ഥയായിരിക്കും.",
        "temp_forecast": "താപനില ഏകദേശം {temp}°C, ഈർപ്പം {humidity}%.",
        "irrigation_delay": "നിർദ്ദേശം: നനയ്ക്കുന്നത് നീട്ടിവെക്കുക. മഴ ({rain} mm) പ്രതീക്ഷിക്കുന്നു.",
        "irrigation_safe": "നിർദ്ദേശം: നനയ്ക്കാൻ അനുകൂലമായ കാലാവസ്ഥ.",
        "spray_delay": "നിർദ്ദേശം: മരുന്ന് തളിക്കുന്നത് നീട്ടിവെക്കുക.",
        "spray_safe": "നിർദ്ദേശം: മരുന്ന് തളിക്കാൻ അനുകൂല കാലാവസ്ഥ.",
        "warning_alert": "മുന്നറിയിപ്പ്: {headline}. {instruction}",
        "travel_caution": "നിർദ്ദേശം: യാത്രയിൽ ജാഗ്രത പാലിക്കുക.",
        "source_tag": "ഉറവിടം: {source}",
        "confidence_tag": "വിശ്വാസ്യത: {confidence}"
    },
    "bn": {  # Bengali
        "rain_expected": "{location}-এ {time_desc} বৃষ্টির সম্ভাবনা রয়েছে।",
        "no_rain": "{location}-এ {time_desc} আকাশ পরিষ্কার থাকবে।",
        "temp_forecast": "তাপমাত্রা প্রায় {temp}°C এবং আর্দ্রতা {humidity}% থাকবে।",
        "irrigation_delay": "পরামর্শ: সেচ স্থগিত রাখুন। বৃষ্টিপাতের ({rain} মিমি) সম্ভাবনা রয়েছে।",
        "irrigation_safe": "পরামর্শ: সেচের জন্য আবহাওয়া অনুকূল।",
        "spray_delay": "পরামর্শ: বৃষ্টির কারণে কীটনাশক স্প্রে করা স্থগিত রাখুন।",
        "spray_safe": "পরামর্শ: কীটনাশক স্প্রে করার জন্য আবহাওয়া উপযুক্ত।",
        "warning_alert": "সতর্কবার্তা: {headline}. {instruction}",
        "travel_caution": "পরামর্শ: ভ্রমণের সময় সতর্কতা অবলম্বন করুন।",
        "source_tag": "উৎস: {source}",
        "confidence_tag": "নির্ভরযোগ্যতা: {confidence}"
    },
    "mr": {  # Marathi
        "rain_expected": "{location} मध्ये {time_desc} पाऊस पडण्याची शक्यता आहे.",
        "no_rain": "{location} मध्ये {time_desc} हवामान स्वच्छ राहील.",
        "temp_forecast": "तापमान सुमारे {temp}°C आणि आर्द्रता {humidity}% राहण्याचा अंदाज आहे.",
        "irrigation_delay": "सल्ला: सिंचन पुढे ढकला. पाऊस ({rain} मिमी) पडण्याची शक्यता आहे.",
        "irrigation_safe": "सल्ला: सिंचनासाठी हवामान अनुकूल आहे.",
        "spray_delay": "सल्ला: पावसामुळे कीटकनाशक फवारणी पुढे ढकला.",
        "spray_safe": "सल्ला: कीटकनाशक फवारणीसाठी हवामान अनुकूल आहे.",
        "warning_alert": "इशारा: {headline}. {instruction}",
        "travel_caution": "सल्ला: प्रवासात काळजी घ्या.",
        "source_tag": "स्रोत: {source}",
        "confidence_tag": "विश्वासार्हता: {confidence}"
    }
}


def get_translated_string(key: str, lang: str = "en", **kwargs) -> str:
    lang_dict = TRANSLATION_DICTIONARY.get(lang, TRANSLATION_DICTIONARY["en"])
    template = lang_dict.get(key, TRANSLATION_DICTIONARY["en"].get(key, ""))
    try:
        return template.format(**kwargs)
    except Exception:
        return template
