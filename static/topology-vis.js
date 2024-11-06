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
        
        // 计算层级信息
        const levels = {};
        Object.entries(data).forEach(([id, node]) => {
            if (!levels[node.level]) {
                levels[node.level] = [];
            }
            levels[node.level].push({id, ...node});
        });
        
        const levelCount = Object.keys(levels).length;
        const levelHeight = this.canvas.height / (levelCount + 1);
        
        // 绘制每一层的节点
        Object.entries(levels).forEach(([level, nodes]) => {
            const y = (parseInt(level) + 1) * levelHeight;
            const nodeWidth = this.canvas.width / (nodes.length + 1);
            
            nodes.forEach((node, index) => {
                const x = (index + 1) * nodeWidth;
                
                // 绘制到父节点的连线
                if (node.parent) {
                    const parentNode = data[node.parent];
                    const parentLevel = parentNode.level;
                    const parentNodes = levels[parentLevel];
                    const parentIndex = parentNodes.findIndex(n => n.id === node.parent);
                    const parentX = (parentIndex + 1) * (this.canvas.width / (parentNodes.length + 1));
                    const parentY = (parentLevel + 1) * levelHeight;
                    
                    ctx.beginPath();
                    ctx.moveTo(x, y);
                    ctx.lineTo(parentX, parentY);
                    ctx.strokeStyle = '#a0aec0';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }
                
                this.drawNode(x, y, node, node.id);
            });
        });
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
        
        results.forEach(result => {
            const div = document.createElement('div');
            div.className = 'result-item p-3 rounded cursor-pointer';
            const filename = result.filename;
            const matches = filename.match(/topology_(\d+)nodes_(\d{8}_\d{6})\.json/);
            const date = new Date(matches[2].replace(/_/, 'T').replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3'));
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