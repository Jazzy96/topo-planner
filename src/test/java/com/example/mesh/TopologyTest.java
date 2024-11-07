package com.example.mesh;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.annotation.JsonProperty;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

public class TopologyTest {
    private static final Logger logger = LoggerFactory.getLogger(TopologyTest.class);
    private static final String API_URL = "http://localhost:8080/generate_topology";
    private static final ObjectMapper mapper = new ObjectMapper();
    private static final int DEFAULT_NODE_COUNT = 10;

    @Test
    public void testTopologyGeneration() throws Exception {
        // 打印当前使用的节点数量
        System.out.println("Running test with node count: " + 
            System.getProperty("nodeCount", String.valueOf(DEFAULT_NODE_COUNT)));
            
        // 生成测试数据
        TestData testData = generateTestData();
        
        // 在转换为JSON之前打印测试数据
        System.out.println("Test data before serialization:");
        System.out.println("Nodes: " + mapper.writeValueAsString(testData.nodes));
        System.out.println("Edges: " + mapper.writeValueAsString(testData.edges));
        
        // 转换为JSON
        String requestBody = mapper.writeValueAsString(Map.of(
            "nodes_json", mapper.writeValueAsString(testData.nodes),
            "edges_json", mapper.writeValueAsString(testData.edges)
        ));

        // 创建HTTP请求
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(API_URL))
            .header("Content-Type", "application/json")
            .header("Accept", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(requestBody))
            .build();

        // 创建一个新的 HttpClient
        HttpClient client = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .build();

        // 发送请求
        HttpResponse<String> response = client.send(request, 
            HttpResponse.BodyHandlers.ofString());

        // 打印格式化的请求和响应信息
        System.out.println("Request body:");
        System.out.println(prettyPrintJson(requestBody));
        System.out.println("\nResponse status: " + response.statusCode());
        System.out.println("Response body:");
        System.out.println(prettyPrintJson(response.body()));

        // 验证响应
        assertEquals(200, response.statusCode(), 
            "Expected status code 200 but got " + response.statusCode() + 
            ". Response body: " + response.body());

        // 验证响应格式
        var responseJson = mapper.readTree(response.body());
        assertTrue(responseJson.has("status"), "Response should have 'status' field");
        assertTrue(responseJson.has("data"), "Response should have 'data' field");
        assertEquals("success", responseJson.get("status").asText(), "Status should be 'success'");
    }

    // 添加用于格式化JSON的辅助方法
    private String prettyPrintJson(String jsonString) {
        try {
            // 如果是嵌套的JSON字符串，先解除转义
            if (jsonString.startsWith("\"") && jsonString.endsWith("\"")) {
                jsonString = jsonString.substring(1, jsonString.length() - 1)
                                     .replace("\\\"", "\"")
                                     .replace("\\\\", "\\");
            }
            
            // 解析JSON
            Object json = mapper.readValue(jsonString, Object.class);
            
            // 格式化输出
            return mapper.writerWithDefaultPrettyPrinter()
                        .writeValueAsString(json);
        } catch (Exception e) {
            logger.error("JSON格式化失败: {}", e.getMessage());
            return jsonString;
        }
    }

    private static class TestData {
        public Map<String, NodeInfo> nodes;
        public Map<String, EdgeInfo> edges;
    }

    private static class NodeInfo {
        public List<Double> gps;
        public double load;
        public Map<String, Map<String, List<Integer>>> channels;
        @JsonProperty("max_eirp")
        public Map<String, Map<String, List<Integer>>> maxEirp;

        public NodeInfo() {}
    }

    private static class EdgeInfo {
        public List<Integer> rssi_6gh;
        public List<Integer> rssi_6gl;

        public EdgeInfo() {}
    }

    // 添加用于计算距离和RSSI的辅助方法
    private double distance(List<Double> pos1, List<Double> pos2) {
        // 使用 Haversine 公式计算两点间距离（单位：米）
        double lat1 = Math.toRadians(pos1.get(0));
        double lon1 = Math.toRadians(pos1.get(1));
        double lat2 = Math.toRadians(pos2.get(0));
        double lon2 = Math.toRadians(pos2.get(1));
        
        double R = 6371e3; // 地球半径（米）
        double dLat = lat2 - lat1;
        double dLon = lon2 - lon1;
        
        double a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                   Math.cos(lat1) * Math.cos(lat2) *
                   Math.sin(dLon/2) * Math.sin(dLon/2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        
        return R * c;
    }

    private double baseRSSI(double distance, double frequency, double txPower, double txGain, double rxGain, double loss) {
        double c = 3e8;
        double fspl = 20 * Math.log10(distance) + 
                     20 * Math.log10(frequency) + 
                     20 * Math.log10(4 * Math.PI / c) + loss;
        return txPower + txGain + rxGain - fspl;
    }

    private EdgeInfo generateEdgeInfo(List<Double> pos1, List<Double> pos2) {
        EdgeInfo edge = new EdgeInfo();
        double dist = distance(pos1, pos2);
        
        // 基础参数
        double txPower = 22;
        double txGain = 7.5;
        double rxGain = 7.5;
        double loss = 8;
        
        // 计算6GL和6GH的RSSI
        double baseL = baseRSSI(dist, 6.15e9, txPower, txGain, rxGain, loss);
        double baseH = baseRSSI(dist, 6.75e9, txPower, txGain, rxGain, loss);
        
        // 添加随机波动（±2dB）
        edge.rssi_6gl = Arrays.asList(
            (int) Math.round(baseL + (Math.random() * 4 - 2)),
            (int) Math.round(baseL + (Math.random() * 4 - 2))
        );
        
        edge.rssi_6gh = Arrays.asList(
            (int) Math.round(baseH + (Math.random() * 4 - 2)),
            (int) Math.round(baseH + (Math.random() * 4 - 2))
        );
        
        return edge;
    }

    private TestData generateTestData() {
        TestData data = new TestData();
        data.nodes = new HashMap<>();
        data.edges = new HashMap<>();

        int nodeCount = Integer.parseInt(
            System.getProperty("nodeCount", String.valueOf(DEFAULT_NODE_COUNT))
        );
        
        // 根节点的GPS坐标
        double rootLat = -36.739546;
        double rootLon = 174.631266;
        
        // 根据节点数量计算合适的覆盖半径（单位：米）
        // 假设每个节点理想覆盖面积 = 总面积 / 节点数
        double totalRadius = Math.min(2000, Math.sqrt(nodeCount) * 300); // 最大2000米
        
        // 存储所有节点的GPS坐标
        List<List<Double>> nodePositions = new ArrayList<>();
        
        // 生成节点数据
        for (int i = 0; i < nodeCount; i++) {
            String nodeId = "SN" + i;
            NodeInfo node = new NodeInfo();
            
            List<Double> gps;
            if (i == 0) {
                // 根节点使用固定坐标
                gps = Arrays.asList(rootLat, rootLon);
            } else {
                // 使用同心圆方式生成其他节点的坐标
                // 计算当前节点所在的层数和该层的节点索引
                int layerIndex = (int)Math.sqrt(i);
                int nodesInThisLayer = layerIndex * 8; // 每层节点数随半径增加
                int nodeIndexInLayer = (i - layerIndex * layerIndex) % nodesInThisLayer;
                
                // 计算当前层的半径（递增）
                double layerRadius = (totalRadius * layerIndex) / Math.sqrt(nodeCount);
                
                // 计算角度（添加随机偏移）
                double angle = (2 * Math.PI * nodeIndexInLayer) / nodesInThisLayer;
                angle += (Math.random() - 0.5) * Math.PI / nodesInThisLayer; // 添加随机偏移
                
                // 添加半径的随机偏移（±20%）
                double radiusWithJitter = layerRadius * (0.8 + Math.random() * 0.4);
                
                // 将极坐标转换为经纬度偏移
                double latOffset = (radiusWithJitter / 111111) * Math.cos(angle);
                double lonOffset = (radiusWithJitter / (111111 * Math.cos(Math.toRadians(rootLat)))) * Math.sin(angle);
                
                gps = Arrays.asList(
                    rootLat + latOffset,
                    rootLon + lonOffset
                );
            }
            
            nodePositions.add(gps);
            node.gps = gps;
            
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
            
            // 打印每个节点的数据
            try {
                System.out.println("Generated node " + nodeId + ": " + 
                    mapper.writeValueAsString(node));
            } catch (Exception e) {
                e.printStackTrace();
            }
            
            data.nodes.put(nodeId, node);
        }

        // 生成边数据 - 使用基于距离的RSSI计算
        for (int i = 0; i < nodeCount; i++) {
            for (int j = i + 1; j < nodeCount; j++) {
                String edgeKey = String.format("SN%d_SN%d", i, j);
                data.edges.put(edgeKey, generateEdgeInfo(nodePositions.get(i), nodePositions.get(j)));
            }
        }

        return data;
    }
}
