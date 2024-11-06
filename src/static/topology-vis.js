class TopologyVisualizer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.resize();
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        this.canvas.width = this.canvas.parentElement.clientWidth - 40;
        this.canvas.height = window.innerHeight - 100;
    }

    drawNode(x, y, node, id) {
        const ctx = this.ctx;
        
        // 绘制节点圆圈
        ctx.beginPath();
        ctx.arc(x, y, 30, 0, Math.PI * 2);
        ctx.fillStyle = node.backhaulBand === 'H' ? '#ff7043' : '#42a5f5';
        ctx.fill();
        ctx.stroke();
        
        // 绘制节点ID
        ctx.fillStyle = 'white';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.font = '14px Arial';
        ctx.fillText(id, x, y);
        
        // 绘制信道和带宽信息
        ctx.fillStyle = 'black';
        ctx.font = '12px Arial';
        const info = `CH:${node.channel.join(',')} BW:${node.bandwidth.join(',')}`;
        ctx.fillText(info, x, y + 45);
    }

    drawTopology(data) {
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
                    ctx.stroke();
                }
                
                this.drawNode(x, y, node, node.id);
            });
        });
    }
}

// 初始化
let visualizer;
let activeResult = null;

async function loadResults() {
    const response = await fetch('/api/results');
    const results = await response.json();
    
    const resultsList = document.getElementById('resultsList');
    resultsList.innerHTML = '';
    
    results.forEach(result => {
        const div = document.createElement('div');
        div.className = 'result-item';
        const filename = result.filename;
        const matches = filename.match(/topology_(\d+)nodes_(\d{8}_\d{6})\.json/);
        div.textContent = `${matches[1]}节点 - ${matches[2].replace('_', ' ')}`;
        
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
}

document.addEventListener('DOMContentLoaded', () => {
    visualizer = new TopologyVisualizer(document.getElementById('canvas'));
    loadResults();
}); 