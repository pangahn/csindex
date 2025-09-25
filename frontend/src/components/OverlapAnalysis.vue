<template>
  <div class="analysis-section">
    <!-- 重合度分析结果 -->
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>重合度分析结果</span>
        </div>
      </template>
      <div v-if="calculationResults.length === 0" class="empty-state">
        <el-empty description="暂无计算结果">
        </el-empty>
      </div>
      <div v-else class="heatmap-wrapper">
        <div class="heatmap-section">
          <h3>重合数量</h3>
          <div id="count-heatmap" class="heatmap"></div>
        </div>
        <div class="heatmap-section">
          <h3>重合权重</h3>
          <div id="weight-heatmap" class="heatmap"></div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import api from '@/api/config';
import * as echarts from 'echarts';

export default {
  name: 'OverlapAnalysis',
  props: {
    selectedIndices: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      calculationResults: [],
      loading: {
        calculation: false
      },
      charts: []
    };
  },
  methods: {
    async calculateOverlap() {
      if (this.selectedIndices.length < 2) {
        this.$message.warning('请至少选择两个指数进行计算');
        return;
      }

      this.loading.calculation = true;

      try {
        const response = await api.post('/api/calculate_overlap', {
          indices: this.selectedIndices
        });

        // 构建包含指数代码的标签数组
        const labelsWithCodes = response.data.names.map((name, index) => {
          const selectedIndex = this.selectedIndices[index];
          return `${name}\n${selectedIndex.code}`;
        });

        // 将标签数组添加到响应数据中
        const resultData = {
          ...response.data,
          labelsWithCodes: labelsWithCodes
        };

        // 清空历史结果，只保留当前计算结果
        this.calculationResults = [resultData];

        // 渲染热力图
        this.$nextTick(() => {
          this.renderHeatmap(
            'count-heatmap',
            resultData.labelsWithCodes,
            resultData.count_matrix,
            '重合数量'
          );
          this.renderHeatmap(
            'weight-heatmap',
            resultData.labelsWithCodes,
            resultData.weight_matrix,
            '重合权重'
          );
        });

        this.$message.success('计算完成');
      } catch (error) {
        console.error('计算重合度失败:', error);
        this.$message.error('计算重合度失败');
      } finally {
        this.loading.calculation = false;
      }
    },
    renderHeatmap(elementId, names, data, title) {
      const chartDom = document.getElementById(elementId);
      const myChart = echarts.init(chartDom);

      const option = {
        tooltip: {
          position: 'top',
          formatter: function(params) {
            const xLabel = names[params.value[0]];
            const yLabel = names[params.value[1]];
            const value = params.value[2];

            // 如果是重合权重，显示2位小数
            const formattedValue = title === '重合权重' ?
              parseFloat(value).toFixed(2) : value;

            return `${xLabel}<br/>${yLabel}<br/>${title}: ${formattedValue}`;
          }
        },
        grid: {
          height: '75%',
          top: '5%',
          left: '15%',
          right: '10%',
          bottom: '20%'
        },
        xAxis: {
          type: 'category',
          data: names,
          splitArea: {
            show: true
          },
          axisLabel: {
            rotate: 45,
            fontSize: 10,
            interval: 0,
            margin: 8
          }
        },
        yAxis: {
          type: 'category',
          data: names,
          splitArea: {
            show: true
          },
          axisLabel: {
            fontSize: 10,
            interval: 0,
            margin: 8
          }
        },
        visualMap: {
          min: 0,
          max: title === '重合数量' ?
            Math.max(...data.flat()) :
            Math.max(...data.flat().map(v => parseFloat(v))),
          calculable: true,
          orient: 'horizontal',
          left: 'center',
          bottom: '0%',
          show: false
        },
        series: [
          {
            name: title,
            type: 'heatmap',
            data: data.map((row, i) =>
              row.map((val, j) => [j, i, val])
            ).flat(),
            label: {
              show: true,
              fontSize: 10,
              color: '#333',
              formatter: function(params) {
                // 如果是重合权重，显示2位小数
                if (title === '重合权重') {
                  return parseFloat(params.value[2]).toFixed(2);
                }
                // 重合数量直接显示整数
                return params.value[2];
              }
            },
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      };

      myChart.setOption(option);
      this.charts.push(myChart);

      // 窗口大小变化时重绘图表
      window.addEventListener('resize', () => {
        myChart.resize();
      });
    },
    // 清理图表资源
    clearCharts() {
      this.charts.forEach(chart => {
        if (chart && !chart.isDisposed()) {
          chart.dispose();
        }
      });
      this.charts = [];
    }
  },
  beforeUnmount() {
    // 组件销毁前清理图表资源
    this.clearCharts();
  }
};
</script>

<style scoped>
.heatmap-container {
  margin-bottom: 30px;
}

.heatmap-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.heatmap-section {
  flex: 1;
  min-width: 300px;
}

.heatmap {
  height: 400px;
  width: 100%;
}

h3 {
  text-align: center;
  margin-bottom: 5px;
  margin-top: 0;
  color: #606266;
}
</style>