from datetime import datetime
from typing import List, Dict, Any, Optional
from app.schemas.weather import (
    UnifiedWeatherResponse, WeatherAnalysis, DayRainSummary, RainAnalysisSummary,
    HourlyForecastPoint, DailyForecastPoint, LocationComparisonItem,
    MultiLocationAnalysis, WhyExplanation
)
from app.schemas.intent import QueryIntent, TimeRange


def get_rain_likelihood_label(prob: int) -> str:
    if prob <= 20:
        return "Very low chance"
    elif prob <= 40:
        return "Low chance"
    elif prob <= 60:
        return "Rain possible"
    elif prob <= 80:
        return "Rain likely"
    else:
        return "Rain very likely"


def format_hour_display(hour: int) -> str:
    if hour == 0:
        return "12 AM"
    elif hour < 12:
        return f"{hour} AM"
    elif hour == 12:
        return "12 PM"
    else:
        return f"{hour - 12} PM"


class WeatherAnalyzer:
    """
    Performs backend numerical and statistical analysis on forecast data
    BEFORE passing structured facts to Gemini.
    Gemini is ONLY responsible for natural language synthesis, NEVER for prediction.
    """

    def analyze(self, weather: UnifiedWeatherResponse, intent: QueryIntent) -> WeatherAnalysis:
        location_name = intent.location.name if intent.location and intent.location.name else weather.location.name
        t_range = intent.time_range or TimeRange()

        horizon_days = t_range.horizon_days or 1
        day_offset = t_range.day_offset or 0

        # Group hourly points by date
        hourly_by_date: Dict[str, List[HourlyForecastPoint]] = {}
        for pt in weather.hourly:
            # pt.time format: "YYYY-MM-DDTHH:00"
            date_key = pt.time.split("T")[0] if "T" in pt.time else pt.time[:10]
            if date_key not in hourly_by_date:
                hourly_by_date[date_key] = []
            hourly_by_date[date_key].append(pt)

        # Build daily summaries
        daily_breakdown: List[DayRainSummary] = []
        available_days = weather.daily

        # Determine index range to analyze
        start_idx = day_offset
        end_idx = min(start_idx + horizon_days, len(available_days))
        if start_idx >= len(available_days):
            start_idx = 0
            end_idx = min(horizon_days, len(available_days))

        for idx in range(start_idx, end_idx):
            d_point = available_days[idx]
            d_date = d_point.date

            # Compute day label
            if idx == 0:
                day_label = "Today"
            elif idx == 1:
                day_label = "Tomorrow"
            else:
                day_label = f"Day {idx + 1}"

            # Hourly points for this day
            day_hours = hourly_by_date.get(d_date, [])

            # Determine peak rain hour and probability
            max_prob = d_point.precipitation_probability_max_pct
            peak_time_str = "Mostly dry"

            if day_hours:
                # Find point with highest rain probability
                peak_pt = max(day_hours, key=lambda p: p.precipitation_probability_pct)
                if peak_pt.precipitation_probability_pct > max_prob:
                    max_prob = peak_pt.precipitation_probability_pct

                if max_prob >= 30:
                    try:
                        hour_num = int(peak_pt.time.split("T")[1].split(":")[0])
                        # Check surrounding hours for a window
                        surrounding = [
                            p for p in day_hours
                            if abs(int(p.time.split("T")[1].split(":")[0]) - hour_num) <= 1
                            and p.precipitation_probability_pct >= max_prob - 10
                        ]
                        if len(surrounding) >= 2:
                            h_min = min(int(p.time.split("T")[1].split(":")[0]) for p in surrounding)
                            h_max = max(int(p.time.split("T")[1].split(":")[0]) for p in surrounding)
                            peak_time_str = f"around {format_hour_display(h_min)}–{format_hour_display(h_max)}"
                        else:
                            peak_time_str = f"around {format_hour_display(hour_num)}"
                    except Exception:
                        peak_time_str = "afternoon/evening"
                else:
                    peak_time_str = "Mostly dry"

            likelihood = get_rain_likelihood_label(max_prob)

            daily_breakdown.append(
                DayRainSummary(
                    date=d_date,
                    day_label=day_label,
                    probability_pct=max_prob,
                    likelihood_label=likelihood,
                    expected_precipitation_mm=d_point.precipitation_sum_mm,
                    condition=d_point.weather_condition,
                    icon=d_point.weather_icon,
                    peak_time=peak_time_str,
                    temperature_max_c=d_point.temperature_max_c,
                    temperature_min_c=d_point.temperature_min_c
                )
            )

        # Aggregate Rain Analysis across the requested horizon
        rain_analysis: Optional[RainAnalysisSummary] = None
        if daily_breakdown:
            rain_possible = any(d.probability_pct >= 30 or d.expected_precipitation_mm >= 0.5 for d in daily_breakdown)
            peak_day = max(daily_breakdown, key=lambda d: d.probability_pct)
            lowest_day = min(daily_breakdown, key=lambda d: d.probability_pct)
            total_precip = round(sum(d.expected_precipitation_mm for d in daily_breakdown), 1)

            # Umbrella recommendation for target period
            target_first_day = daily_breakdown[0]
            if target_first_day.probability_pct >= 40 or target_first_day.expected_precipitation_mm >= 1.0:
                umbrella_rec = f"Yes, carrying an umbrella is recommended ({target_first_day.day_label} has a {target_first_day.probability_pct}% chance of precipitation)."
            elif target_first_day.probability_pct >= 25:
                umbrella_rec = f"You might consider carrying a small umbrella as a precaution ({target_first_day.probability_pct}% chance of rain)."
            else:
                umbrella_rec = f"No umbrella needed ({target_first_day.day_label} is expected to be mostly dry with only {target_first_day.probability_pct}% rain chance)."

            rain_analysis = RainAnalysisSummary(
                rain_possible=rain_possible,
                highest_probability=peak_day.probability_pct,
                highest_probability_date=peak_day.date,
                highest_probability_day_label=peak_day.day_label,
                highest_probability_time=peak_day.peak_time,
                total_expected_precipitation_mm=total_precip,
                best_day_to_avoid_rain=f"{lowest_day.day_label} ({lowest_day.probability_pct}% chance)",
                highest_rain_risk=f"{peak_day.day_label} ({peak_day.peak_time}, {peak_day.probability_pct}% chance)",
                umbrella_recommendation=umbrella_rec
            )

        # Specific Hourly Focus Window (e.g., 6 PM or tomorrow evening)
        hourly_focus_window = None
        hourly_focus_details = None

        target_date = available_days[day_offset].date if day_offset < len(available_days) else available_days[0].date
        day_hourly = hourly_by_date.get(target_date, [])

        if t_range.target_hour is not None and day_hourly:
            # Match exact target hour
            target_h = t_range.target_hour
            matched_pt = next((p for p in day_hourly if f"T{target_h:02d}:00" in p.time), None)
            if matched_pt:
                hourly_focus_window = f"{format_hour_display(target_h)}"
                hourly_focus_details = {
                    "time": matched_pt.time,
                    "hour_label": format_hour_display(target_h),
                    "temperature_c": matched_pt.temperature_c,
                    "precipitation_probability_pct": matched_pt.precipitation_probability_pct,
                    "precipitation_mm": matched_pt.precipitation_mm,
                    "condition": matched_pt.weather_condition,
                    "humidity_pct": matched_pt.relative_humidity_pct,
                    "wind_kmh": matched_pt.wind_speed_kmh
                }
        elif t_range.hour_start is not None and t_range.hour_end is not None and day_hourly:
            # Match hour range (e.g. tomorrow evening 17:00 to 21:00)
            window_pts = [
                p for p in day_hourly
                if t_range.hour_start <= int(p.time.split("T")[1].split(":")[0]) <= t_range.hour_end
            ]
            if window_pts:
                peak_window_pt = max(window_pts, key=lambda p: p.precipitation_probability_pct)
                h_peak = int(peak_window_pt.time.split("T")[1].split(":")[0])
                hourly_focus_window = f"{format_hour_display(t_range.hour_start)} to {format_hour_display(t_range.hour_end)}"
                hourly_focus_details = {
                    "window_label": hourly_focus_window,
                    "max_rain_probability_pct": peak_window_pt.precipitation_probability_pct,
                    "peak_time": format_hour_display(h_peak),
                    "precipitation_sum_mm": round(sum(p.precipitation_mm for p in window_pts), 1),
                    "condition": peak_window_pt.weather_condition,
                    "average_temp_c": round(sum(p.temperature_c for p in window_pts) / len(window_pts), 1)
                }

        # Temperature Comparison (Today vs Tomorrow)
        temp_comparison = None
        if len(available_days) >= 2:
            today_d = available_days[0]
            tomorrow_d = available_days[1]
            diff = round(tomorrow_d.temperature_max_c - today_d.temperature_max_c, 1)
            temp_comparison = {
                "today_max_c": today_d.temperature_max_c,
                "today_min_c": today_d.temperature_min_c,
                "today_condition": today_d.weather_condition,
                "tomorrow_max_c": tomorrow_d.temperature_max_c,
                "tomorrow_min_c": tomorrow_d.temperature_min_c,
                "tomorrow_condition": tomorrow_d.weather_condition,
                "difference_c": diff,
                "is_tomorrow_hotter": diff > 0.5,
                "is_tomorrow_cooler": diff < -0.5
            }

        # Outdoor Activity Recommendation
        outdoor_rec = None
        if daily_breakdown:
            # Score each day for outdoor suitability: lowest rain prob, reasonable temp
            scored = sorted(daily_breakdown, key=lambda d: (d.probability_pct, d.expected_precipitation_mm))
            best = scored[0]
            outdoor_rec = {
                "best_day": best.day_label,
                "date": best.date,
                "rain_probability_pct": best.probability_pct,
                "expected_rain_mm": best.expected_precipitation_mm,
                "max_temp_c": best.temperature_max_c,
                "condition": best.condition,
                "reason": f"{best.day_label} has the lowest rain probability ({best.probability_pct}%) and mostly dry conditions."
            }

        # Check for Why Explanation
        why_exp = None
        if intent.relational_goal == "why_explanation" or "why" in intent.question_focus:
            why_exp = self.explain_weather_phenomenon(weather, intent)

        return WeatherAnalysis(
            location=location_name,
            period=t_range.relative_day or "today",
            horizon_days=horizon_days,
            weather_variable=intent.weather_variable,
            question_focus=intent.question_focus,
            rain_analysis=rain_analysis,
            daily_breakdown=daily_breakdown,
            hourly_focus_window=hourly_focus_window,
            hourly_focus_details=hourly_focus_details,
            temperature_comparison=temp_comparison,
            outdoor_recommendation=outdoor_rec,
            why_explanation=why_exp
        )

    def explain_weather_phenomenon(self, weather: UnifiedWeatherResponse, intent: QueryIntent) -> WhyExplanation:
        curr = weather.current
        today = weather.daily[0] if weather.daily else None
        var = intent.weather_variable
        drivers: List[str] = []

        if var in ["rain", "umbrella"] or (today and today.precipitation_probability_max_pct >= 40) or curr.precipitation_mm > 0:
            phenomenon = "Rainfall and Precipitation"
            primary = "High atmospheric moisture and active convective cloud formation"
            if curr.relative_humidity_pct >= 65:
                drivers.append(f"Elevated relative humidity ({curr.relative_humidity_pct}%) saturated the boundary layer.")
            if curr.cloud_cover_pct is not None and curr.cloud_cover_pct >= 50:
                drivers.append(f"Heavy cloud coverage ({curr.cloud_cover_pct}%) indicating dense tropospheric cloud formations.")
            if curr.surface_pressure_hpa and curr.surface_pressure_hpa < 1012.0:
                drivers.append(f"Relatively low surface pressure ({curr.surface_pressure_hpa} hPa) facilitating convective air lifting.")
            if not drivers:
                drivers.append(f"Precipitation probability currently calculated at {today.precipitation_probability_max_pct if today else curr.precipitation_probability_pct}%.")
            verdict = f"Rain in {weather.location.name} is primarily driven by high atmospheric moisture ({curr.relative_humidity_pct}% humidity) and significant cloud cover."
        elif var in ["temperature", "heat"] or curr.temperature_c >= 35:
            phenomenon = "Elevated Temperature"
            primary = "Strong surface solar heating and low cloud attenuation"
            if curr.cloud_cover_pct is not None and curr.cloud_cover_pct < 35:
                drivers.append(f"Clear to partly cloudy skies ({curr.cloud_cover_pct}% cloud cover) allowing unobstructed solar irradiance.")
            if curr.relative_humidity_pct < 50:
                drivers.append(f"Dry air mass (humidity {curr.relative_humidity_pct}%) promoting rapid diurnal heating.")
            drivers.append(f"Ambient temperature reached {curr.temperature_c}°C (feels like {curr.feels_like_c}°C).")
            verdict = f"The heat in {weather.location.name} is caused by intense solar radiation combined with low cloud cover and dry atmospheric conditions."
        elif var == "wind" or curr.wind_speed_kmh >= 30:
            phenomenon = "High Winds"
            primary = "Horizontal pressure gradient across the region"
            drivers.append(f"Sustained wind speeds of {curr.wind_speed_kmh} km/h with gusts up to {curr.wind_gusts_kmh or round(curr.wind_speed_kmh * 1.3, 1)} km/h.")
            if curr.surface_pressure_hpa:
                drivers.append(f"Local surface barometric pressure measured at {curr.surface_pressure_hpa} hPa.")
            verdict = f"Strong winds in {weather.location.name} ({curr.wind_speed_kmh} km/h) are driven by regional atmospheric pressure differences."
        else:
            phenomenon = f"Current Conditions ({curr.weather_condition})"
            primary = "Prevailing regional meteorological patterns"
            drivers.append(f"Temperature: {curr.temperature_c}°C, Humidity: {curr.relative_humidity_pct}%, Wind: {curr.wind_speed_kmh} km/h.")
            verdict = f"Current weather in {weather.location.name} is {curr.weather_condition} under prevailing seasonal conditions."

        return WhyExplanation(
            phenomenon=phenomenon,
            primary_factor=primary,
            meteorological_drivers=drivers,
            observed_parameters={
                "temperature_c": curr.temperature_c,
                "humidity_pct": curr.relative_humidity_pct,
                "cloud_cover_pct": curr.cloud_cover_pct,
                "surface_pressure_hpa": curr.surface_pressure_hpa,
                "wind_speed_kmh": curr.wind_speed_kmh,
                "precipitation_mm": curr.precipitation_mm
            },
            verdict=verdict
        )

    def analyze_multi_locations(
        self,
        weather_map: Dict[str, UnifiedWeatherResponse],
        intent: QueryIntent
    ) -> MultiLocationAnalysis:
        items: List[LocationComparisonItem] = []
        for name, w in weather_map.items():
            curr = w.current
            today = w.daily[0] if w.daily else None
            max_t = today.temperature_max_c if today else curr.temperature_c
            min_t = today.temperature_min_c if today else curr.temperature_c
            rain_p = today.precipitation_probability_max_pct if today else (curr.precipitation_probability_pct or 0)
            precip = today.precipitation_sum_mm if today else curr.precipitation_mm
            cond = today.weather_condition if today else curr.weather_condition
            icon = today.weather_icon if today else curr.weather_icon

            items.append(
                LocationComparisonItem(
                    location=name,
                    latitude=w.location.latitude,
                    longitude=w.location.longitude,
                    temperature_c=curr.temperature_c,
                    temperature_max_c=max_t,
                    temperature_min_c=min_t,
                    condition=cond,
                    icon=icon,
                    rain_probability_pct=rain_p,
                    precipitation_mm=precip,
                    wind_speed_kmh=curr.wind_speed_kmh,
                    humidity_pct=curr.relative_humidity_pct,
                    summary_verdict=f"{icon} {cond}, {curr.temperature_c}°C, {rain_p}% rain"
                )
            )

        goal = intent.relational_goal or "compare"
        criteria = intent.comparison_criteria or intent.weather_variable or "overall"
        activity = intent.activity

        direct_answer = ""
        ranking_winner = None
        route_details = None

        # 1. Route scenario (e.g. from X to Y)
        if intent.origin_location and intent.destination_location and len(items) >= 2:
            orig_name = intent.origin_location.name.lower()
            dest_name = intent.destination_location.name.lower()
            orig_item = next((it for it in items if orig_name in it.location.lower()), items[0])
            dest_item = next((it for it in items if dest_name in it.location.lower()), items[1])

            direct_answer = (
                f"🚗 **Route Weather: {orig_item.location} to {dest_item.location}**\n\n"
                f"• **Origin ({orig_item.location}):** {orig_item.icon} {orig_item.condition}, {orig_item.temperature_c}°C, "
                f"Rain probability: {orig_item.rain_probability_pct}%, Wind: {orig_item.wind_speed_kmh} km/h.\n"
                f"• **Destination ({dest_item.location}):** {dest_item.icon} {dest_item.condition}, {dest_item.temperature_c}°C, "
                f"Rain probability: {dest_item.rain_probability_pct}%, Wind: {dest_item.wind_speed_kmh} km/h.\n\n"
            )
            if dest_item.rain_probability_pct >= 50 or dest_item.precipitation_mm >= 2.0:
                direct_answer += f"⚠️ **Travel Advisory:** Expect wet conditions and possible road spray near {dest_item.location}."
            elif dest_item.temperature_c > orig_item.temperature_c + 4:
                direct_answer += f"💡 **Travel Note:** It will be noticeably warmer in {dest_item.location} (+{dest_item.temperature_c - orig_item.temperature_c:.1f}°C)."
            elif dest_item.temperature_c < orig_item.temperature_c - 4:
                direct_answer += f"💡 **Travel Note:** It will be noticeably cooler in {dest_item.location} ({dest_item.temperature_c - orig_item.temperature_c:.1f}°C)."
            else:
                direct_answer += f"✅ **Travel Advisory:** Favorable driving weather expected across this route."

            route_details = {
                "origin": orig_item.location,
                "destination": dest_item.location,
                "temp_diff": round(dest_item.temperature_c - orig_item.temperature_c, 1),
                "rain_alert": dest_item.rain_probability_pct >= 50
            }
            ranking_winner = dest_item.location

        # 2. Temperature comparison (e.g. "is X hotter than Y?" or "which is warmer?")
        elif criteria in ["temperature", "heat"] or "hot" in goal or "warm" in goal:
            sorted_by_temp = sorted(items, key=lambda x: x.temperature_max_c, reverse=True)
            hotter = sorted_by_temp[0]
            cooler = sorted_by_temp[-1]
            ranking_winner = hotter.location
            diff = round(hotter.temperature_max_c - cooler.temperature_max_c, 1)

            if len(items) == 2:
                if diff < 0.8:
                    direct_answer = f"🌡️ **{hotter.location} and {cooler.location} have very similar temperatures** (around {hotter.temperature_max_c}°C vs {cooler.temperature_max_c}°C)."
                else:
                    direct_answer = f"🌡️ **{hotter.location} is warmer than {cooler.location}** with highs of **{hotter.temperature_max_c}°C** compared to **{cooler.temperature_max_c}°C** (+{diff}°C difference)."
            else:
                direct_answer = f"🌡️ **{hotter.location} is the warmest** among the locations with highs of **{hotter.temperature_max_c}°C**, while {cooler.location} is the coolest at {cooler.temperature_max_c}°C."

        # 3. Rain / avoid rain comparison
        elif criteria in ["rain", "precipitation", "umbrella"] or goal == "avoid":
            if goal == "avoid" or "less" in criteria or "least" in criteria:
                sorted_by_rain = sorted(items, key=lambda x: (x.rain_probability_pct, x.precipitation_mm))
                best = sorted_by_rain[0]
                worst = sorted_by_rain[-1]
                ranking_winner = best.location
                direct_answer = (
                    f"☀️ **{best.location} has the lowest chance of rain** ({best.rain_probability_pct}%, {best.condition}) "
                    f"compared to {worst.location} ({worst.rain_probability_pct}% chance of rain, {worst.condition})."
                )
            else:
                sorted_by_rain = sorted(items, key=lambda x: (x.rain_probability_pct, x.precipitation_mm), reverse=True)
                highest = sorted_by_rain[0]
                lowest = sorted_by_rain[-1]
                ranking_winner = highest.location
                direct_answer = (
                    f"🌧️ **{highest.location} has the highest rain risk** ({highest.rain_probability_pct}% chance, expected {highest.precipitation_mm} mm) "
                    f"compared to {lowest.location} ({lowest.rain_probability_pct}% chance)."
                )

        # 4. General / outdoor / activity ranking
        else:
            def score_loc(it: LocationComparisonItem) -> float:
                temp_penalty = abs(it.temperature_c - 24.0) * 1.5
                rain_penalty = it.rain_probability_pct * 0.8
                wind_penalty = max(0.0, it.wind_speed_kmh - 25.0) * 1.2
                return -(temp_penalty + rain_penalty + wind_penalty)

            sorted_items = sorted(items, key=score_loc, reverse=True)
            best = sorted_items[0]
            ranking_winner = best.location

            act_str = f" for {activity}" if activity else ""
            direct_answer = (
                f"🏆 **{best.location} has the best overall weather{act_str}** with {best.condition}, "
                f"comfortable temperature of {best.temperature_c}°C, and only {best.rain_probability_pct}% rain chance."
            )

        return MultiLocationAnalysis(
            locations=items,
            relational_goal=goal,
            comparison_criteria=criteria,
            activity=activity,
            direct_answer=direct_answer,
            ranking_or_winner=ranking_winner,
            route_details=route_details
        )

    def generate_deterministic_answer(self, analysis: WeatherAnalysis, query: str) -> str:
        """
        High-fidelity deterministic response generator that answers the user's
        EXACT question cleanly without boilerplate or hallucination.
        Serves as the zero-downtime fallback whenever LLM is unavailable.
        """
        # Multi-Location comparison / ranking / route
        if analysis.multi_location:
            ml = analysis.multi_location
            lines = [ml.direct_answer, ""]
            lines.append("📍 **Location Comparison Details:**")
            for it in ml.locations:
                lines.append(f"• **{it.location}:** {it.icon} {it.condition} | High: {it.temperature_max_c}°C | Rain: {it.rain_probability_pct}% | Wind: {it.wind_speed_kmh} km/h")
            return "\n".join(lines)

        # Why explanation
        if analysis.why_explanation:
            why = analysis.why_explanation
            lines = [
                f"🔍 **Meteorological Explanation: {why.phenomenon} in {analysis.location}**\n",
                f"**Primary Driver:** {why.primary_factor}\n",
                "**Key Meteorological Factors:**"
            ]
            for d in why.meteorological_drivers:
                lines.append(f"• {d}")
            lines.append(f"\n💡 **Summary:** {why.verdict}")
            return "\n".join(lines)

        focus = analysis.question_focus
        var = analysis.weather_variable
        days = analysis.daily_breakdown
        r_anal = analysis.rain_analysis

        # 1. Multi-day rain query (e.g. "Is there any chance of rain in the next 4 days?")
        if analysis.horizon_days > 1 and (var in ["rain", "umbrella", "outdoor"] or focus in ["rain_possibility", "compare_rain", "peak_rain_time"]):
            lines = []
            if r_anal and r_anal.rain_possible:
                lines.append(f"🌧️ **Rain is possible over the next {analysis.horizon_days} days in {analysis.location}.**\n")
            else:
                lines.append(f"☀️ **Mostly dry weather is expected over the next {analysis.horizon_days} days in {analysis.location}.**\n")

            for d in days:
                lines.append(f"• **{d.day_label}:** {d.icon} {d.likelihood_label}, up to {d.probability_pct}% ({d.peak_time})")

            lines.append("")
            if r_anal:
                if analysis.outdoor_recommendation:
                    lines.append(f"👉 **Best day to avoid rain:** {analysis.outdoor_recommendation['best_day']}")
                lines.append(f"👉 **Highest rain risk:** {r_anal.highest_rain_risk}")

            return "\n".join(lines)

        # 2. Specific time query (e.g. "Will it rain tomorrow evening?" or "Weather at 6 PM")
        if analysis.hourly_focus_details:
            details = analysis.hourly_focus_details
            if "hour_label" in details:
                hr_label = details["hour_label"]
                prob = details["precipitation_probability_pct"]
                temp = details["temperature_c"]
                cond = details["condition"]
                target_day_label = days[0].day_label if days else "today"
                if prob >= 40:
                    return f"🌧️ At **{hr_label}** {target_day_label.lower()} in {analysis.location}, rain is possible with a **{prob}% chance of precipitation** ({temp}°C, {cond})."
                else:
                    return f"☀️ At **{hr_label}** {target_day_label.lower()} in {analysis.location}, conditions look mostly dry with only a **{prob}% chance of precipitation** ({temp}°C, {cond})."
            elif "window_label" in details:
                w_label = details["window_label"]
                prob = details["max_rain_probability_pct"]
                peak_time = details["peak_time"]
                cond = details["condition"]
                target_day_label = days[0].day_label if days else "tomorrow"
                if prob >= 40:
                    return f"🌧️ Rain is likely {target_day_label.lower()} during the evening ({w_label}), peaking **{peak_time}** at **{prob}% chance of precipitation** ({cond})."
                else:
                    return f"☀️ Mostly dry conditions expected {target_day_label.lower()} during the evening ({w_label}), with rain probability peaking at only **{prob}%**."

        # 3. Peak rain time query (e.g. "When will it rain?" / "When is rain most likely?")
        if focus == "peak_rain_time" and r_anal:
            if r_anal.highest_probability >= 30:
                return f"🌧️ In **{analysis.location}**, rain is most likely on **{r_anal.highest_probability_day_label}**, with precipitation probability peaking **{r_anal.highest_probability_time}** at **{r_anal.highest_probability}%**."
            else:
                return f"☀️ In **{analysis.location}**, no significant rain is expected over the requested period. The highest precipitation probability is only **{r_anal.highest_probability}%** ({r_anal.highest_probability_day_label})."

        # 4. Umbrella query (e.g. "Should I carry an umbrella tomorrow?")
        if var == "umbrella" or focus == "carry_umbrella":
            if r_anal and r_anal.umbrella_recommendation:
                return f"☂️ {r_anal.umbrella_recommendation}"

        # 5. Best outdoor day query
        if focus == "best_outdoor_day" and analysis.outdoor_recommendation:
            rec = analysis.outdoor_recommendation
            return f"🏕️ **{rec['best_day']}** looks like the best option for outdoor activities in {analysis.location}. It has the lowest rain chance ({rec['rain_probability_pct']}%), expected highs around {rec['max_temp_c']}°C, and mostly dry conditions."

        # 6. Temperature comparison (e.g. "Is tomorrow hotter than today?")
        if focus == "compare_temperature" and analysis.temperature_comparison:
            tc = analysis.temperature_comparison
            diff = tc["difference_c"]
            if tc["is_tomorrow_hotter"]:
                return f"🌡️ Yes, tomorrow will be warmer than today in {analysis.location}. Expected high is **{tc['tomorrow_max_c']}°C** compared to today's **{tc['today_max_c']}°C** (+{diff}°C)."
            elif tc["is_tomorrow_cooler"]:
                return f"🌡️ No, tomorrow will be slightly cooler than today in {analysis.location}. Expected high is **{tc['tomorrow_max_c']}°C** compared to today's **{tc['today_max_c']}°C** ({diff}°C)."
            else:
                return f"🌡️ Tomorrow's temperature in {analysis.location} will be very similar to today, with highs around **{tc['tomorrow_max_c']}°C** (today: {tc['today_max_c']}°C)."

        # 7. Single day rain query ("Will it rain today?" or "Will it rain tomorrow?")
        if var == "rain" or focus == "rain_possibility":
            target = days[0] if days else None
            if target:
                if target.probability_pct >= 50:
                    return f"🌧️ **Yes, rain is likely {target.day_label.lower()} in {analysis.location}.** Precipitation probability reaches **{target.probability_pct}%** ({target.peak_time}) with expected rainfall around {target.expected_precipitation_mm} mm ({target.condition})."
                elif target.probability_pct >= 30:
                    return f"🌦️ **Rain is possible {target.day_label.lower()} in {analysis.location}.** There is a **{target.probability_pct}% chance of precipitation** ({target.peak_time}) with expected rain of {target.expected_precipitation_mm} mm ({target.condition})."
                else:
                    return f"☀️ **No significant rain expected {target.day_label.lower()} in {analysis.location}.** The precipitation probability is only **{target.probability_pct}%**, with mostly dry conditions ({target.condition})."

        # 8. Single day general forecast ("What's the weather tomorrow?")
        if days:
            target = days[0]
            rain_note = f"{target.probability_pct}% chance of rain" if target.probability_pct >= 20 else "mostly dry"
            return f"{target.icon} In **{analysis.location}**, {target.day_label.lower()} will be **{target.condition}**. Highs around **{target.temperature_max_c}°C**, lows near **{target.temperature_min_c}°C**, with a **{rain_note}**."

        return f"Weather forecast for {analysis.location} is available based on current meteorological data."


weather_analyzer = WeatherAnalyzer()
