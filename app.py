from datetime import datetime

import akshare as ak
import numpy as np
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="frontend/dist")
CORS(app)

cache = {
    "cs_list": None,
    "cni_list": None,
    "index_data": {},
}


def get_index_components_data(code, source):
    """
    获取指数成分券数据的统一函数

    Args:
        code (str): 指数代码
        source (str): 指数来源，'cs' 或 'cni'

    Returns:
        list: 标准化后的成分券数据列表

    Raises:
        ValueError: 当指数源不支持时
        Exception: 当获取数据失败时
    """
    cache_key = f"{source}_{code}"
    if cache_key in cache["index_data"]:
        return cache["index_data"][cache_key]

    try:
        if source == "cs":
            df = ak.index_stock_cons_weight_csindex(symbol=code)
            df["成分券代码"] = df["成分券代码"].astype(str).str.zfill(6)
            df = df.rename(columns={"成分券名称": "成分券简称"})
            components = df.to_dict("records")

        elif source == "cni":
            df = ak.index_detail_cni(symbol=code, date="202508")  # 禁止修改date参数
            df["样本代码"] = df["样本代码"].astype(str).str.zfill(6)
            df = df.rename(columns={"样本代码": "成分券代码", "样本简称": "成分券简称"})
            components = df.to_dict("records")

        else:
            raise ValueError(f"不支持的指数源: {source}")

        cache["index_data"][cache_key] = components
        return components

    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"获取{source}指数{code}成分股失败: {str(e)}")


def calculate_overlap_matrices(index_to_stocks, index_to_weights, names):
    """
    计算指数重合度矩阵

    Args:
        index_to_stocks (dict): 指数名称到成分股集合的映射
        index_to_weights (dict): 指数名称到成分股权重的映射
        names (list): 指数名称列表

    Returns:
        tuple: (count_matrix, weight_matrix) 重合数量矩阵和权重矩阵
    """
    n = len(names)
    count_matrix = np.zeros((n, n), dtype=int)
    weight_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            # 获取两个指数的成分股集合
            stocks_i = index_to_stocks[names[i]]
            stocks_j = index_to_stocks[names[j]]

            # 计算重合成分股
            overlap_stocks = stocks_i & stocks_j
            count_matrix[i, j] = len(overlap_stocks)

            # 计算重合成分股权重之和
            weights_i = index_to_weights[names[i]]
            weights_j = index_to_weights[names[j]]

            overlap_weight = 0.0
            for stock in overlap_stocks:
                overlap_weight += weights_i.get(stock, 0) + weights_j.get(stock, 0)

            weight_matrix[i, j] = round(overlap_weight, 4)

    weight_matrix = weight_matrix / 2  # 权重值除以2

    return count_matrix, weight_matrix


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)


@app.route("/api/index_providers", methods=["GET"])
def get_index_providers():
    """获取指数提供商列表"""
    providers = [
        {"id": "cs", "name": "中证指数"},
        {"id": "cni", "name": "国证指数"},
    ]
    return jsonify(providers)


@app.route("/api/indices/<provider>", methods=["GET"])
def get_indices(provider):
    """获取指定提供商的指数列表"""
    try:
        if provider == "cs":
            if cache["cs_list"] is None:
                cache["cs_list"] = ak.index_csindex_all()[["指数代码", "指数简称"]].to_dict("records")
            return jsonify(cache["cs_list"])
        elif provider == "cni":
            if cache["cni_list"] is None:
                cache["cni_list"] = ak.index_all_cni()[["指数代码", "指数简称"]].to_dict("records")
            return jsonify(cache["cni_list"])
        else:
            return jsonify({"error": "不支持的指数提供商"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/index_components", methods=["GET"])
def get_index_components():
    """获取指数成分股"""
    try:
        code = request.args.get("code")
        source = request.args.get("source")

        if not code or not source:
            return jsonify({"error": "缺少必要参数"}), 400

        components = get_index_components_data(code, source)
        return jsonify(components)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/index_heatmap", methods=["POST"])
def get_index_heatmap():
    """获取指数成分券热力图数据"""
    try:
        data = request.json
        selected_indices = data.get("indices", [])

        if not selected_indices:
            return jsonify({"error": "请选择至少一个指数"}), 400

        all_stocks = set()
        index_components = {}
        index_info_dict = {}

        for index_info in selected_indices:
            code = index_info["code"]
            name = index_info["name"]
            source = index_info["source"]

            # 存储指数完整信息
            index_info_dict[name] = {"code": code, "name": name, "source": source}

            # 检查缓存
            cache_key = f"{source}_{code}"
            if cache_key in cache["index_data"]:
                components = cache["index_data"][cache_key]
            else:
                # 使用统一的辅助函数获取成分股数据
                try:
                    components = get_index_components_data(code, source)
                except ValueError as e:
                    return jsonify({"error": str(e)}), 400
                except Exception as e:
                    return jsonify({"error": str(e)}), 500

            # 收集成分券信息
            index_stocks = {}
            for comp in components:
                stock_code = comp.get("成分券代码")
                stock_name = comp.get("成分券简称", "")
                weight = comp.get("权重", 0)
                if stock_code:
                    all_stocks.add(stock_code)
                    index_stocks[stock_code] = {"name": stock_name, "weight": weight}

            index_components[name] = index_stocks

        # 1. 行维度排序：按成分券个数从多到少，相同时按指数代码升序
        index_names_with_count = []
        for name in index_info_dict.keys():
            count = len(index_components[name])
            code = index_info_dict[name]["code"]
            index_names_with_count.append((name, count, code))

        # 排序：成分券个数降序，指数代码升序
        index_names_with_count.sort(key=lambda x: (-x[1], x[2]))
        sorted_index_names = [item[0] for item in index_names_with_count]

        # 2. 列维度排序：优先展示第1行指数的成分券，其他成分券按代码升序
        if sorted_index_names:
            first_index_stocks = set(index_components[sorted_index_names[0]].keys())
            other_stocks = all_stocks - first_index_stocks

            # 第一行指数的成分券按代码升序
            first_stocks_sorted = sorted(list(first_index_stocks))
            # 其他成分券按代码升序
            other_stocks_sorted = sorted(list(other_stocks))

            # 合并：第一行指数的成分券在前，其他成分券在后
            stock_list = first_stocks_sorted + other_stocks_sorted
        else:
            stock_list = sorted(list(all_stocks))

        # 构建热力图矩阵（按排序后的顺序）
        matrix = []
        for index_name in sorted_index_names:
            row = []
            for stock_code in stock_list:
                if stock_code in index_components[index_name]:
                    weight = index_components[index_name][stock_code]["weight"]
                    row.append(weight)
                else:
                    row.append(0)
            matrix.append(row)

        # 构建股票信息列表
        stock_info = []
        for stock_code in stock_list:
            # 从任一包含该股票的指数中获取股票名称
            stock_name = stock_code
            for index_name in sorted_index_names:
                if stock_code in index_components[index_name]:
                    stock_name = index_components[index_name][stock_code]["name"]
                    break
            stock_info.append({"code": stock_code, "name": stock_name})

        # 构建指数信息列表（包含简称和代码）
        indices_info = []
        for index_name in sorted_index_names:
            info = index_info_dict[index_name]
            indices_info.append(
                {
                    "name": info["name"],
                    "code": info["code"],
                    "source": info["source"],
                    "component_count": len(index_components[index_name]),
                }
            )

        result = {
            "indices": sorted_index_names,
            "indices_info": indices_info,
            "stocks": stock_info,
            "matrix": matrix,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/calculate_overlap", methods=["POST"])
def calculate_overlap():
    """计算指数重合度"""
    try:
        data = request.json
        selected_indices = data.get("indices", [])

        if not selected_indices or len(selected_indices) < 2:
            return jsonify({"error": "至少需要选择两个指数"}), 400

        # 获取所有指数的成分股
        index_to_stocks = {}
        index_to_weights = {}
        names = []

        for index_info in selected_indices:
            code = index_info["code"]
            name = index_info["name"]
            source = index_info["source"]
            names.append(name)

            # 检查缓存
            cache_key = f"{source}_{code}"
            if cache_key in cache["index_data"]:
                components = cache["index_data"][cache_key]
            else:
                # 使用统一的辅助函数获取成分股数据
                try:
                    components = get_index_components_data(code, source)
                except ValueError as e:
                    return jsonify({"error": str(e)}), 400
                except Exception as e:
                    return jsonify({"error": str(e)}), 500

            # 提取成分股代码和权重
            stocks = set()
            weights = {}
            for comp in components:
                stock_code = comp.get("成分券代码")
                if stock_code:
                    stocks.add(stock_code)
                    weights[stock_code] = comp.get("权重", 0)

            index_to_stocks[name] = stocks
            index_to_weights[name] = weights

        # 计算交集矩阵
        count_matrix, weight_matrix = calculate_overlap_matrices(index_to_stocks, index_to_weights, names)

        # 构建结果
        result = {
            "names": names,
            "count_matrix": count_matrix.tolist(),
            "weight_matrix": weight_matrix.tolist(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5001)
