import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet, FlatList, TouchableOpacity } from "react-native";
import { listAssessments } from "../services/api";

export default function HistoryScreen({ navigation }: any) {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => { listAssessments().then(setItems); }, []);

  return (
    <View style={s.wrap}>
      <Text style={s.title}>History</Text>
      <FlatList data={items} keyExtractor={i => i.assessment_id}
        renderItem={({ item }) => (
          <TouchableOpacity style={s.item} onPress={() => navigation.navigate("Assessment", { id: item.assessment_id })}>
            <Text style={s.ntrp}>NTRP {item.overall_ntrp}</Text>
            <Text style={s.date}>{item.created_at?.slice(0, 10)}</Text>
          </TouchableOpacity>
        )}
        ListEmptyComponent={<Text style={s.empty}>No assessments yet</Text>}
      />
    </View>
  );
}

const s = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: "#f5f5f5", padding: 16 },
  title: { fontSize: 22, fontWeight: "bold", marginTop: 40, marginBottom: 16 },
  item: { backgroundColor: "#fff", borderRadius: 12, padding: 16, marginBottom: 10, flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  ntrp: { fontSize: 20, fontWeight: "bold", color: "#4CAF50" },
  date: { fontSize: 14, color: "#999" },
  empty: { textAlign: "center", marginTop: 60, fontSize: 16, color: "#999" },
});
