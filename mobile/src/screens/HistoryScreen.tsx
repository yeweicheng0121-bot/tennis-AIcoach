import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet, FlatList, TouchableOpacity } from "react-native";
import { listAssessments } from "../services/api";

const C = { bg: "#0A0D14", card: "#111827", accent: "#00D68F", text: "#FFFFFF", muted: "#6B7280", sub: "#9CA3AF", border: "#1F2937" };

export default function HistoryScreen({ navigation }: any) {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => { listAssessments().then(setItems); }, []);

  return (
    <View style={styles.wrap}>
      <Text style={styles.title}>History</Text>
      <FlatList data={items} keyExtractor={i => i.assessment_id}
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.card} onPress={() => navigation.navigate("Assessment", { id: item.assessment_id })} activeOpacity={0.7}>
            <View>
              <Text style={styles.ntrp}>{item.overall_ntrp ? `NTRP ${item.overall_ntrp}` : "—"}</Text>
              <Text style={styles.date}>{item.created_at?.slice(0, 10)}</Text>
            </View>
            <View style={styles.tagRow}>
              {(item.weaknesses || []).slice(0, 2).map((w: string, i: number) => <View key={i} style={styles.tag}><Text style={styles.tagText}>{w}</Text></View>)}
            </View>
            <Text style={styles.arrow}>→</Text>
          </TouchableOpacity>
        )}
        ListEmptyComponent={<Text style={styles.empty}>No assessments yet</Text>}
        contentContainerStyle={{ paddingBottom: 20 }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: C.bg, padding: 20 },
  title: { fontSize: 28, fontWeight: "800", color: C.text, marginTop: 50, marginBottom: 20 },
  card: { backgroundColor: C.card, borderRadius: 16, padding: 18, marginBottom: 10, flexDirection: "row", alignItems: "center", borderWidth: 1, borderColor: C.border },
  ntrp: { fontSize: 18, fontWeight: "700", color: C.accent },
  date: { fontSize: 11, color: C.muted, marginTop: 4 },
  tagRow: { flex: 1, flexDirection: "row", marginLeft: 16, gap: 6 },
  tag: { backgroundColor: "rgba(245,158,11,0.1)", paddingHorizontal: 10, paddingVertical: 4, borderRadius: 6 },
  tagText: { color: "#F59E0B", fontSize: 11, fontWeight: "600" },
  arrow: { fontSize: 18, color: C.muted, marginLeft: 8 },
  empty: { textAlign: "center", color: C.muted, fontSize: 15, marginTop: 80 },
});
