import React from "react";
import { View, Text, StyleSheet } from "react-native";

export default function RadarChart({ data }: { data: Record<string, number> }) {
  return (
    <View style={s.wrap}>
      <Text style={s.title}>Technique Radar</Text>
      {Object.entries(data).map(([label, value]) => (
        <View key={label} style={s.row}>
          <Text style={s.lbl}>{label}</Text>
          <View style={s.track}><View style={[s.fill, { width: `${value}%` }]} /></View>
          <Text style={s.val}>{value}</Text>
        </View>
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  wrap: { backgroundColor: "#fff", borderRadius: 12, padding: 16, marginBottom: 12 },
  title: { fontSize: 16, fontWeight: "600", marginBottom: 12 },
  row: { flexDirection: "row", alignItems: "center", marginBottom: 8 },
  lbl: { width: 70, fontSize: 13, color: "#666" },
  track: { flex: 1, height: 12, backgroundColor: "#eee", borderRadius: 6, overflow: "hidden" },
  fill: { height: "100%", backgroundColor: "#4CAF50", borderRadius: 6 },
  val: { width: 36, textAlign: "right", fontSize: 13, fontWeight: "600" },
});
