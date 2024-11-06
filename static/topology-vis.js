class TopologyVisualizer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.resize();
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        this.canvas.width = this.canvas.parentElement.clientWidth - 40;
        this.canvas.height = Math.max(400, window.innerHeight - 200);
        if (this.lastData) {
            this.drawTopology(this.lastData);
        }
    }

    drawNode(x, y, node, id) {
        const ctx = this.ctx;
        const radius = 25;
        
        // 绘制节点圆圈
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fillStyle = node.backhaulBand === 'H' ? '#f6ad55' : '#63b3ed';
        ctx.fill();
        ctx.strokeStyle = '#2c5282';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        // 绘制节点ID
        ctx.fillStyle = '#2d3748';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.font = 'bold 14px Arial';
        ctx.fillText(id, x, y);
        
        // 绘制信道和带宽信息
        ctx.fillStyle = '#2d3748';
        ctx.font = '12px Arial';
        const channelInfo = `CH:${node.channel.join(',')}`;
        const bwInfo = `BW:${node.bandwidth.join(',')}`;
        ctx.fillText(channelInfo, x, y + radius + 15);
        ctx.fillText(bwInfo, x, y + radius + 30);
    }

    drawTopology(data) {
        this.lastData = data;
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 构建树形结构
        const root = this.buildTree(data);
        
        // 计算节点位置
        this.calculateNodePositions(root, 0, 0, this.canvas.width, this.canvas.height / 2);
        
        // 绘制连线和节点
        this.drawTreeConnections(root);
        this.drawTreeNodes(root);
    }

    buildTree(data) {
        const nodes = {};
        let root = null;

        // 创建所有节点
        for (const [id, nodeData] of Object.entries(data)) {
            nodes[id] = { ...nodeData, id, children: [] };
            if (nodeData.parent === null) {
                root = nodes[id];
            }
        }

        // 构建树形结构
        for (const node of Object.values(nodes)) {
            if (node.parent !== null) {
                nodes[node.parent].children.push(node);
            }
        }

        return root;
    }

    calculateNodePositions(node, depth, startAngle, endAngle, radius) {
        const angleRange = endAngle - startAngle;
        const childCount = node.children.length;
        
        node.x = this.canvas.width / 2 + radius * Math.cos(startAngle + angleRange / 2);
        node.y = this.canvas.height / 2 + radius * Math.sin(startAngle + angleRange / 2);

        if (childCount > 0) {
            const childAngleRange = angleRange / childCount;
            for (let i = 0; i < childCount; i++) {
                const childStartAngle = startAngle + i * childAngleRange;
                const childEndAngle = childStartAngle + childAngleRange;
                this.calculateNodePositions(node.children[i], depth + 1, childStartAngle, childEndAngle, radius + 100);
            }
        }
    }

    drawTreeConnections(node) {
        const ctx = this.ctx;
        for (const child of node.children) {
            ctx.beginPath();
            ctx.moveTo(node.x, node.y);
            ctx.lineTo(child.x, child.y);
            ctx.strokeStyle = '#a0aec0';
            ctx.lineWidth = 2;
            ctx.stroke();
            this.drawTreeConnections(child);
        }
    }

    drawTreeNodes(node) {
        this.drawNode(node.x, node.y, node, node.id);
        for (const child of node.children) {
            this.drawTreeNodes(child);
        }
    }
}

let visualizer;
let activeResult = null;

async function loadResults() {
    try {
        const response = await fetch('/api/results');
        const results = await response.json();
        
        const resultsList = document.getElementById('resultsList');
        resultsList.innerHTML = '';
        
        // 对结果按日期降序排序
        results.sort((a, b) => {
            const dateA = new Date(a.filename.match(/(\d{8}_\d{6})/)[1].replace(/_/, 'T').replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3'));
            const dateB = new Date(b.filename.match(/(\d{8}_\d{6})/)[1].replace(/_/, 'T').replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3'));
            return dateB - dateA;
        });
        
        results.forEach(result => {
            const div = document.createElement('div');
            div.className = 'result-item p-3 rounded cursor-pointer';
            const filename = result.filename;
            const matches = filename.match(/topology_(\d+)nodes_(\d{8}_\d{6})\.json/);
            const dateStr = matches[2].replace(/_/, 'T').replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3');
            const date = new Date(dateStr);
            div.innerHTML = `
                <div class="font-semibold">${matches[1]} 节点</div>
                <div class="text-sm text-gray-600">${date.toLocaleString()}</div>
            `;
            
            div.onclick = () => {
                document.querySelectorAll('.result-item').forEach(item => {
                    item.classList.remove('active');
                });
                div.classList.add('active');
                visualizer.drawTopology(result.data.data);
                activeResult = result;
            };
            
            resultsList.appendChild(div);
        });
        
        // 显示最新的结果
        if (results.length > 0) {
            resultsList.firstChild.click();
        }
    } catch (error) {
        console.error('加载结果失败:', error);
        alert('加载结果失败，请检查网络连接并刷新页面。');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    visualizer = new TopologyVisualizer(document.getElementById('canvas'));
    loadResults();
});