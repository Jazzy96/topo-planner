package com.example.mesh;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import java.util.*;

public class TopologyTest {
    private static final String API_URL = "http://localhost:8080/generate_topology";
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
        // TODO: 添加更多验证逻辑
    }

    private static class TestData {
        Map<String, NodeInfo> nodes;
        Map<String, EdgeInfo> edges;
    }

    private static class NodeInfo {
        List<Double> gps;
        double load;
        Map<String, Map<String, List<Integer>>> channels;
        Map<String, Map<String, List<Integer>>> maxEirp;
    }

    private static class EdgeInfo {
        List<Integer> rssi_6gh;
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
            
            // 6GL频段类似...
            
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
