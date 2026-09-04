import httpx
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_dynamic_scenarios():
    client = httpx.Client(timeout=30.0)

    print("=" * 60)
    print("TEST 1: Dynamic Location 1 - Amaravati + Crop: Paddy")
    res1 = client.get(f"{BASE_URL}/advisories?sector=agriculture&latitude=16.5131&longitude=80.5165&crop=paddy")
    assert res1.status_code == 200, f"Error: {res1.status_code}"
    d1 = res1.json()
    print(f"Location: {d1['location']} ({d1['latitude']}, {d1['longitude']})")
    print(f"Sector: {d1['sector']}, Overall Risk: {d1['overall_risk']} (Score: {d1['overall_risk_score']})")
    for a in d1['advisories']:
        print(f"  [{a['icon']} {a['title']}] -> Verdict: {a['recommendation']} (Risk: {a['risk_level']})")
        print(f"     Trigger: {a['weather_trigger']}")
        print(f"     Basis: {a['basis'][0]}")
        print(f"     Valid: {a['valid_until']} | Source: {', '.join(a['sources'])}")

    print("\n" + "=" * 60)
    print("TEST 2: Dynamic Location 2 - Hyderabad + Crop: Paddy (Verify weather changes)")
    res2 = client.get(f"{BASE_URL}/advisories?sector=agriculture&latitude=17.3850&longitude=78.4867&crop=paddy")
    assert res2.status_code == 200
    d2 = res2.json()
    print(f"Location: {d2['location']} ({d2['latitude']}, {d2['longitude']})")
    for a in d2['advisories']:
        print(f"  [{a['icon']} {a['title']}] -> Verdict: {a['recommendation']} (Risk: {a['risk_level']})")
        print(f"     Trigger: {a['weather_trigger']}")

    print("\n" + "=" * 60)
    print("TEST 3: Same Location (Hyderabad) + Crop: Cotton (Verify crop-specific rules apply)")
    res3 = client.get(f"{BASE_URL}/advisories?sector=agriculture&latitude=17.3850&longitude=78.4867&crop=cotton")
    assert res3.status_code == 200
    d3 = res3.json()
    print(f"Location: {d3['location']}, Crop: Cotton")
    for a in d3['advisories']:
        print(f"  [{a['icon']} {a['title']}] -> Verdict: {a['recommendation']} (Risk: {a['risk_level']})")
        print(f"     Trigger: {a['weather_trigger']}")

    print("\n" + "=" * 60)
    print("TEST 4: Marine Sector (Visakhapatnam Coast) - Verify Wave Limitation Note")
    res4 = client.get(f"{BASE_URL}/advisories?sector=marine&latitude=17.6868&longitude=83.2185")
    assert res4.status_code == 200
    d4 = res4.json()
    m_adv = d4['advisories'][0]
    print(f"Title: {m_adv['title']}, Verdict: {m_adv['recommendation']}")
    print(f"Limitations: {m_adv['limitations']}")

    print("\n" + "=" * 60)
    print("TEST 5: Aviation / Drone Sector (Hyderabad) - Verify General Suitability Note")
    res5 = client.get(f"{BASE_URL}/advisories?sector=aviation&latitude=17.3850&longitude=78.4867")
    assert res5.status_code == 200
    d5 = res5.json()
    av_adv = d5['advisories'][0]
    print(f"Title: {av_adv['title']}, Verdict: {av_adv['recommendation']}")
    print(f"Limitations: {av_adv['limitations']}")

    print("\n" + "=" * 60)
    print("TEST 6: 4-Day Horizon Agriculture (Warangal + Cotton)")
    res6 = client.get(f"{BASE_URL}/advisories?sector=agriculture&latitude=17.9689&longitude=79.5941&crop=cotton&horizon_days=4")
    assert res6.status_code == 200
    d6 = res6.json()
    adv_multi = d6['advisories'][0]
    print(f"Title: {adv_multi['title']}, Crop: {adv_multi['crop']}")
    print("4-Day Breakdown:")
    for b in adv_multi['horizon_breakdown']:
        print(f"  {b['day']}: Irrigation: {b['irrigation_verdict']}, Spraying: {b['spraying_verdict']} ({b['condition']}, Rain: {b['rain_probability_pct']}%)")

    print("\n" + "=" * 60)
    print("TEST 7: Chat Query - 'Should I irrigate my paddy tomorrow in Amaravati?'")
    chat_res1 = client.post(f"{BASE_URL}/chat", json={"message": "Should I irrigate my paddy tomorrow in Amaravati?"})
    assert chat_res1.status_code == 200
    c1 = chat_res1.json()
    print(f"Location: {c1['location']}")
    print(f"Answer:\n{c1['answer']}")
    print(f"Advisories payload count: {len(c1['advisories'])}")

    print("\n" + "=" * 60)
    print("TEST 8: Chat Query - 'Can I spray pesticide on cotton crop today in Warangal?'")
    chat_res2 = client.post(f"{BASE_URL}/chat", json={"message": "Can I spray pesticide on cotton crop today in Warangal?"})
    assert chat_res2.status_code == 200
    c2 = chat_res2.json()
    print(f"Location: {c2['location']}")
    print(f"Answer:\n{c2['answer']}")

    print("\n" + "=" * 60)
    print("TEST 9: Chat Query - 'What should I do for my paddy over the next 4 days in Hyderabad?'")
    chat_res3 = client.post(f"{BASE_URL}/chat", json={"message": "What should I do for my paddy over the next 4 days in Hyderabad?"})
    assert chat_res3.status_code == 200
    c3 = chat_res3.json()
    print(f"Location: {c3['location']}")
    print(f"Answer:\n{c3['answer']}")

    print("\n" + "=" * 60)
    print("ALL DYNAMIC SECTOR ADVISORY TESTS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    test_dynamic_scenarios()
