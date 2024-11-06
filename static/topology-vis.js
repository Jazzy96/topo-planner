class TopologyVisualizer {
  constructor(canvas) {
      this.canvas = canvas;
      this.ctx = canvas.getContext('2d');
      this.resize();
      window.addEventListener('resize', () => this.resize());
  }

  resize() {
      this.canvas.width = this.canvas.parentElement.clientWidth - 40;
      this.canvas.height = Math.max(600, window.innerHeight - 200);
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

      // 找到根节点
      const root = Object.entries(data).find(([_, node]) => node.parent === null)[0];
      
      // 计算节点位置
      const nodePositions = this.calculateNodePositions(data, root);

      // 绘制连线和节点
      this.drawConnections(data, nodePositions);
      Object.entries(nodePositions).forEach(([id, pos]) => {
          this.drawNode(pos.x, pos.y, data[id], id);
      });
  }

  calculateNodePositions(data, rootId, x = this.canvas.width / 2, y = 50, level = 0) {
      const positions = {};
      const node = data[rootId];
      positions[rootId] = { x, y };

      const children = Object.entries(data).filter(([_, n]) => n.parent === rootId);
      if (children.length > 0) {
          const levelWidth = this.canvas.width / (level + 2);
          const startX = x - (levelWidth * (children.length - 1)) / 2;
          children.forEach(([childId], index) => {
              const childX = startX + levelWidth * index;
              const childY = y + 100;
              Object.assign(positions, this.calculateNodePositions(data, childId, childX, childY, level + 1));
          });
      }

      return positions;
  }

  drawConnections(data, positions) {
      const ctx = this.ctx;
      Object.entries(data).forEach(([id, node]) => {
          if (node.parent) {
              const startPos = positions[node.parent];
              const endPos = positions[id];
              ctx.beginPath();
              ctx.moveTo(startPos.x, startPos.y);
              ctx.lineTo(endPos.x, endPos.y);
              ctx.strokeStyle = '#a0aec0';
              ctx.lineWidth = 2;
              ctx.stroke();
          }
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
          const matches = filename.match(/topology_(\d+)nodes_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})\.json/);
          if (matches) {
              const [_, nodeCount, year, month, day, hour, minute, second] = matches;
              const date = new Date(year, month - 1, day, hour, minute, second);
              div.innerHTML = `
                  <div class="font-semibold">${nodeCount} 节点</div>
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
          }
      });
      
      // 显示最新的结果
      if (results.length > 0) {
          resultsList.lastChild.click();
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