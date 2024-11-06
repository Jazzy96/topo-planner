package com.example.mesh;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.annotation.JsonProperty;
import org.junit.jupiter.api.Test;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import java.util.*;

public class TopologyTest {
    private static final String API_URL = "http://localhost:1212/generate_topology";
    private static final ObjectMapper mapper = new ObjectMapper();

    @Test
    public void testTopologyGeneration() throws Exception {
        // 生成测试数据
        TestData testData = generateTestData();
        
        // 转换为JSON
        String requestBody = mapper.writeValueAsString(Map.of(
            "nodes_json", mapper.writeValueAsString(testData.nodes),
            "edges_json", mapper.writeValueAsString(testData.edges)
        ));

        // 发送HTTP请求
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(API_URL))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(requestBody))
            .build();

        HttpResponse<String> response = client.send(request, 
            HttpResponse.BodyHandlers.ofString());

        // 验证结果
        assert response.statusCode() == 200;
        
        // 解析响应
        Map<String, Object> result = mapper.readValue(response.body(), Map.class);
        
        // 验证响应格式
        assert result.containsKey("status");
        assert "success".equals(result.get("status"));
        assert result.containsKey("data");
        
        // 获取拓扑数据
        Map<String, Map<String, Object>> topology = (Map<String, Map<String, Object>>) result.get("data");
        
        // 基本验证
        assert topology.size() == 5;  // 验证节点数量
        
        // 验证每个节点的数据结构
        for (Map.Entry<String, Map<String, Object>> entry : topology.entrySet()) {
            String nodeId = entry.getKey();
            Map<String, Object> nodeData = entry.getValue();
            
            // 验证必要字段
            assert nodeData.containsKey("parent");
            assert nodeData.containsKey("backhaulBand");
            assert nodeData.containsKey("level");
            assert nodeData.containsKey("channel");
            assert nodeData.containsKey("bandwidth");
            assert nodeData.containsKey("maxEirp");
            
            // 验证层级关系
            Integer level = (Integer) nodeData.get("level");
            String parent = (String) nodeData.get("parent");
            if (level == 0) {
                assert parent == null;
            } else {
                assert parent != null;
                assert topology.containsKey(parent);
                assert (Integer) topology.get(parent).get("level") == level - 1;
            }
            
            // 验证信道分配
            List<Integer> channels = (List<Integer>) nodeData.get("channel");
            List<Integer> bandwidths = (List<Integer>) nodeData.get("bandwidth");
            List<Integer> eirps = (List<Integer>) nodeData.get("maxEirp");
            
            assert channels.size() == bandwidths.size();
            assert channels.size() == eirps.size();
            
            // 验证带宽值
            for (Integer bandwidth : bandwidths) {
                assert Arrays.asList(20, 40, 80, 160).contains(bandwidth);
            }
            
            // 验证EIRP值范围
            for (Integer eirp : eirps) {
                assert eirp >= 0 && eirp <= 36;
            }
        }
        
        // 验证拓扑连通性
        Set<String> visited = new HashSet<>();
        String root = null;
        for (Map.Entry<String, Map<String, Object>> entry : topology.entrySet()) {
            if (entry.getValue().get("parent") == null) {
                root = entry.getKey();
                break;
            }
        }
        assert root != null;
        
        // DFS验证连通性
        verifyConnectivity(root, topology, visited);
        assert visited.size() == topology.size();
    }

    private void verifyConnectivity(String nodeId, 
                                  Map<String, Map<String, Object>> topology, 
                                  Set<String> visited) {
        visited.add(nodeId);
        for (Map.Entry<String, Map<String, Object>> entry : topology.entrySet()) {
            String currentId = entry.getKey();
            Map<String, Object> nodeData = entry.getValue();
            if (!visited.contains(currentId) && nodeId.equals(nodeData.get("parent"))) {
                verifyConnectivity(currentId, topology, visited);
            }
        }
    }

    private static class TestData {
        Map<String, NodeInfo> nodes;
        Map<String, EdgeInfo> edges;
    }

    private static class NodeInfo {
        @JsonProperty("gps")
        List<Double> gps;
        
        @JsonProperty("load")
        double load;
        
        @JsonProperty("channels")
        Map<String, Map<String, List<Integer>>> channels;
        
        @JsonProperty("maxEirp")
        Map<String, Map<String, List<Integer>>> maxEirp;
    }

    private static class EdgeInfo {
        @JsonProperty("rssi_6gh")
        List<Integer> rssi_6gh;
        
        @JsonProperty("rssi_6gl")
        List<Integer> rssi_6gl;
    }

    private TestData generateTestData() {
        TestData data = new TestData();
        data.nodes = new HashMap<>();
        data.edges = new HashMap<>();

        // 生成节点数据
        for (int i = 0; i < 5; i++) {
            String nodeId = "SN" + i;
            NodeInfo node = new NodeInfo();
            
            // 生成GPS坐标
            node.gps = Arrays.asList(
                30.0 + Math.random(), // 经度
                120.0 + Math.random() // 纬度
            );
            
            // 生成负载
            node.load = Math.random() * 500; // 0-500 Mbps
            
            // 生成信道信息
            node.channels = new HashMap<>();
            node.maxEirp = new HashMap<>();
            
            // 6GH频段
            Map<String, List<Integer>> channels6gh = new HashMap<>();
            Map<String, List<Integer>> eirp6gh = new HashMap<>();
            
            channels6gh.put("160M", Arrays.asList(143));
            channels6gh.put("80M", Arrays.asList(135, 151, 167));
            channels6gh.put("40M", Arrays.asList(123, 131, 139, 147, 155, 163, 171, 179));
            
            eirp6gh.put("160M", Arrays.asList(36));
            eirp6gh.put("80M", Arrays.asList(36, 36, 36));
            eirp6gh.put("40M", Arrays.asList(36, 36, 36, 36, 36, 36, 36, 36));
            
            node.channels.put("6GH", channels6gh);
            node.maxEirp.put("6GH", eirp6gh);
            
            // 6GL频段
            Map<String, List<Integer>> channels6gl = new HashMap<>();
            Map<String, List<Integer>> eirp6gl = new HashMap<>();
            
            channels6gl.put("160M", Arrays.asList(15));
            channels6gl.put("80M", Arrays.asList(7, 23, 39));
            channels6gl.put("40M", Arrays.asList(3, 11, 19, 27, 35, 43, 51, 59));
            channels6gl.put("20M", Arrays.asList(1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49, 53, 57, 61));
            
            eirp6gl.put("160M", Arrays.asList(36));
            eirp6gl.put("80M", Arrays.asList(36, 36, 36));
            eirp6gl.put("40M", Arrays.asList(36, 36, 36, 36, 36, 36, 36, 36));
            eirp6gl.put("20M", Arrays.asList(36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 36));
            
            node.channels.put("6GL", channels6gl);
            node.maxEirp.put("6GL", eirp6gl);
            
            data.nodes.put(nodeId, node);
        }

        // 生成边数据
        for (int i = 0; i < 5; i++) {
            for (int j = i + 1; j < 5; j++) {
                String edgeKey = String.format("SN%d_SN%d", i, j);
                EdgeInfo edge = new EdgeInfo();
                
                // 生成RSSI值（-40到-80之间）
                edge.rssi_6gh = Arrays.asList(
                    -40 - (int)(Math.random() * 40),
                    -40 - (int)(Math.random() * 40)
                );
                edge.rssi_6gl = Arrays.asList(
                    -40 - (int)(Math.random() * 40),
                    -40 - (int)(Math.random() * 40)
                );
                
                data.edges.put(edgeKey, edge);
            }
        }

        return data;
    }
}
