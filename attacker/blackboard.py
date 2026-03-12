import json
import time

class Blackboard:
    def __init__(self):
        self.state = {
            "target_ip":      "localhost",
            "target_urls":    [],
            "open_ports":     [],
            "vulnerabilities": [],
            "logs":           [],
            "current_phase":  "RECON",
            "selected_scenario": None,
            "mission_status": "ONGOING"
        }

    def read_state(self):
        return self.state

    def update_key(self, key, value):
        if key in self.state:
            if isinstance(self.state[key], list) and isinstance(value, list):
                current_set = set(self.state[key])
                new_set     = set(value)
                self.state[key] = list(current_set.union(new_set))
            else:
                self.state[key] = value
            self.log_event(f"UPDATE: '{key}' guncellendi -> {value}")
        else:
            self.log_event(f"ERROR: '{key}' Blackboard'da tanimli degil!")

    def log_event(self, message):
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.state["logs"].append(log_entry)
        print(f"📋 [BLACKBOARD] {log_entry}")

    def get_summary_for_llm(self):
        """
        LLM'e sadece karar vermesi için gereken minimal özeti gönderir.
        Tüm logları değil, sadece mission_status ve kritik flag'leri gönderir.
        Bu sayede LLM log gürültüsünden etkilenmez.
        """
        # Kritik log keyword'lerini kontrol et
        all_logs = self.state.get("logs", [])
        log_text = " ".join(all_logs).upper()

        has_compromised = "SYSTEM_COMPROMISED" in log_text
        has_blocked     = "ATTACK_BLOCKED"     in log_text

        summary = {
            "phase":          self.state["current_phase"],
            "ports":          self.state["open_ports"],
            "vulns":          self.state["vulnerabilities"],
            "urls":           self.state["target_urls"],
            "mission_status":      self.state["mission_status"],
            "selected_scenario":   self.state.get("selected_scenario"),
            # Logların tamamı yerine sadece kritik flag'ler
            "system_compromised": has_compromised,
            "attack_blocked":     has_blocked,
        }
        return json.dumps(summary)


if __name__ == "__main__":
    bb = Blackboard()
    bb.update_key("open_ports", [5000])
    bb.update_key("open_ports", [8813])
    print("LLM Özeti:", bb.get_summary_for_llm())