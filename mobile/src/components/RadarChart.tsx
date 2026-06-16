import React from "react";
import { View, Text, StyleSheet } from "react-native";

const C = { card: "#111827", accent: "#00D68F", text: "#FFFFFF", muted: "#6B7280", sub: "#9CA3AF", border: "#1F2937", track: "#1A1F2E" };

const MAX = 100;

export default function RadarChart({ data }: { data: Record<string, number> }) {
  return (
    <View style={styles.wrap}>
      <Text style={styles.title}>TECHNIQUE BREAKDOWN</Text>
      {Object.entries(data).map(([label, value]) => {
        const pct = Math.min(value, MAX);
        const color = value === 0 ? C.muted : pct >= 70 ? C.accent : pct >= 40 ? "#F59E0B" : "#EF4444";
        return (
          <View key={label} style={styles.row}>
            <Text style={styles.lbl}>{label}</Text>
            <View style={styles.track}>
              <View style={[styles.fill, { width: `${pct}%`, backgroundColor: color }]} />
            </View>
            <Text style={[styles.val, { color }]}>{value || "—"}</Text>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { backgroundColor: C.card, borderRadius: 16, padding: 18, marginBottom: 12, borderWidth: 1, borderColor: C.border },
  title: { fontSize: 11, fontWeight: "700", color: C.sub, letterSpacing: 1.5, marginBottom: 14 },
  row: { flexDirection: "row", alignItems: "center", marginBottom: 10 },
  lbl: { width: 78, fontSize: 12, fontWeight: "600", color: C.sub },
  track: { flex: 1, height: 8, backgroundColor: C.track, borderRadius: 4, overflow: "hidden" },
  fill: { height: "100%", borderRadius: 4 },
  val: { width: 32, textAlign: "right", fontSize: 14, fontWeight: "700", marginLeft: 8 },
});
