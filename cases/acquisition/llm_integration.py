"""
LLM集成模块 - 支持调用大语言模型进行内容理解和分析
支持：
1. 本地部署的开源模型（Qwen、ChatGLM、Ollama等）
2. 云端API（OpenAI、DeepSeek等，可选）
"""

import os
import json
import re
import requests
from typing import Dict, Optional, List
from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """LLM基类"""
    
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """生成文本"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查LLM是否可用"""
        pass


class OllamaLLM(BaseLLM):
    """Ollama本地模型实现
    
    Ollama是一个轻量级的本地模型部署工具，支持多种开源模型。
    安装：https://ollama.ai/
    使用：ollama run qwen:1.8b
    
    支持的模型：
    - qwen:1.8b - 阿里通义千问1.8B（推荐）
    - qwen:7b - 通义千问7B
    - chatglm3 - 清华ChatGLM3
    - llama2 - Meta Llama2
    - mistral - Mistral AI
    """
    
    def __init__(self, model: str = "qwen2.5:0.5b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip('/')
        self._available = None
    
    def is_available(self) -> bool:
        """检查Ollama服务是否可用"""
        if self._available is not None:
            return self._available
        
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                # 检查模型是否已下载
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                # 检查模型是否存在（支持模糊匹配，如qwen:1.8b匹配qwen）
                self._available = any(self.model.split(':')[0] in name for name in model_names)
                if not self._available:
                    print(f"提示: 模型 {self.model} 未下载，请运行: ollama pull {self.model}")
                return self._available
        except Exception as e:
            print(f"Ollama服务不可用: {e}")
            print("请确保Ollama已安装并运行: ollama serve")
            self._available = False
            return False
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """使用Ollama生成文本"""
        if not self.is_available():
            raise ValueError(f"Ollama服务不可用或模型 {self.model} 未下载")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.3,
                        "top_p": 0.9
                    }
                },
                timeout=180
            )
            response.raise_for_status()
            return response.json().get('response', '')
        except Exception as e:
            raise RuntimeError(f"Ollama调用失败: {str(e)}")


class QwenLocalLLM(BaseLLM):
    """Qwen本地模型实现（使用Transformers）
    
    直接使用HuggingFace Transformers加载Qwen模型。
    支持的模型：
    - Qwen/Qwen1.5-1.8B-Chat - 1.8B参数（推荐，速度快）
    - Qwen/Qwen1.5-7B-Chat - 7B参数（效果更好）
    
    安装依赖：
    pip install transformers torch accelerate
    """
    
    def __init__(self, model_name: str = "Qwen/Qwen1.5-1.8B-Chat", device: str = "auto"):
        self.model_name = model_name
        self.device = device
        self._model = None
        self._tokenizer = None
    
    def _load_model(self):
        """延迟加载模型"""
        if self._model is None:
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                print(f"正在加载模型 {self.model_name}...")
                
                self._tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    trust_remote_code=True
                )
                
                self._model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    device_map=self.device,
                    trust_remote_code=True
                ).eval()
                
                print(f"模型 {self.model_name} 加载完成")
            except ImportError:
                raise ImportError(
                    "请安装必要的库:\n"
                    "pip install transformers torch accelerate\n"
                    "或使用Ollama: ollama run qwen:1.8b"
                )
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            return True
        except ImportError:
            return False
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """使用Qwen模型生成文本"""
        self._load_model()
        
        try:
            # 构建对话格式
            messages = [
                {"role": "system", "content": "你是一个专业的Linux内核问题分析专家，擅长从技术文章中提取结构化的问题案例信息。"},
                {"role": "user", "content": prompt}
            ]
            
            text = self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            model_inputs = self._tokenizer([text], return_tensors="pt").to(self._model.device)
            
            generated_ids = self._model.generate(
                model_inputs.input_ids,
                max_new_tokens=max_tokens,
                temperature=0.3,
                top_p=0.9,
                do_sample=True
            )
            
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]
            
            response = self._tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
            return response
        except Exception as e:
            raise RuntimeError(f"Qwen模型生成失败: {str(e)}")


class ChatGLMLocalLLM(BaseLLM):
    """ChatGLM本地模型实现
    
    使用THUDM的ChatGLM模型。
    支持的模型：
    - THUDM/chatglm3-6b - ChatGLM3-6B
    
    安装依赖：
    pip install transformers torch accelerate
    """
    
    def __init__(self, model_name: str = "THUDM/chatglm3-6b", device: str = "auto"):
        self.model_name = model_name
        self.device = device
        self._model = None
        self._tokenizer = None
    
    def _load_model(self):
        """延迟加载模型"""
        if self._model is None:
            try:
                from transformers import AutoTokenizer, AutoModel
                
                print(f"正在加载模型 {self.model_name}...")
                
                self._tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    trust_remote_code=True
                )
                
                self._model = AutoModel.from_pretrained(
                    self.model_name,
                    device_map=self.device,
                    trust_remote_code=True
                ).half().eval()
                
                print(f"模型 {self.model_name} 加载完成")
            except ImportError:
                raise ImportError(
                    "请安装必要的库:\n"
                    "pip install transformers torch accelerate\n"
                    "或使用Ollama: ollama run chatglm3"
                )
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        try:
            from transformers import AutoTokenizer, AutoModel
            return True
        except ImportError:
            return False
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """使用ChatGLM模型生成文本"""
        self._load_model()
        
        try:
            response, _ = self._model.chat(
                self._tokenizer,
                prompt,
                history=[],
                max_length=max_tokens + len(prompt),
                temperature=0.3
            )
            return response
        except Exception as e:
            raise RuntimeError(f"ChatGLM模型生成失败: {str(e)}")


class VLLMLocalLLM(BaseLLM):
    """vLLM本地模型实现
    
    vLLM是一个高性能的推理引擎，支持CPU和GPU推理。
    支持的模型：
    - Qwen/Qwen1.5-1.8B-Chat - 1.8B参数（推荐，速度快）
    - Qwen/Qwen1.5-7B-Chat - 7B参数（效果更好）
    - THUDM/chatglm3-6b - ChatGLM3-6B
    
    安装依赖：
    pip install vllm
    
    CPU推理：
    pip install vllm
    export VLLM_TARGET_DEVICE=cpu
    """
    
    def __init__(self, model_name: str = "Qwen/Qwen1.5-1.8B-Chat", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._llm = None
        self._sampling_params = None
    
    def _load_model(self):
        """延迟加载模型"""
        if self._llm is None:
            try:
                from vllm import LLM, SamplingParams
                
                print(f"正在加载vLLM模型 {self.model_name}...")
                
                # 配置vLLM参数
                if self.device == "cpu":
                    # CPU推理配置
                    self._llm = LLM(
                        model=self.model_name,
                        device="cpu",
                        trust_remote_code=True,
                        dtype="float32",  # CPU使用float32
                        enforce_eager=True,  # CPU模式需要
                    )
                else:
                    # GPU推理配置
                    self._llm = LLM(
                        model=self.model_name,
                        trust_remote_code=True,
                        dtype="float16",
                    )
                
                # 配置采样参数
                self._sampling_params = SamplingParams(
                    temperature=0.3,
                    top_p=0.9,
                    max_tokens=2000
                )
                
                print(f"vLLM模型 {self.model_name} 加载完成")
            except ImportError:
                raise ImportError(
                    "请安装vLLM库:\n"
                    "pip install vllm\n"
                    "CPU推理: export VLLM_TARGET_DEVICE=cpu"
                )
    
    def is_available(self) -> bool:
        """检查vLLM是否可用"""
        try:
            import vllm
            return True
        except ImportError:
            return False
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """使用vLLM生成文本"""
        self._load_model()
        
        try:
            # 更新max_tokens
            if self._sampling_params.max_tokens != max_tokens:
                from vllm import SamplingParams
                self._sampling_params = SamplingParams(
                    temperature=0.3,
                    top_p=0.9,
                    max_tokens=max_tokens
                )
            
            # 构建对话格式
            messages = [
                {"role": "system", "content": "你是一个专业的Linux内核问题分析专家，擅长从技术文章中提取结构化的问题案例信息。"},
                {"role": "user", "content": prompt}
            ]
            
            # 使用vLLM生成
            outputs = self._llm.chat(messages, sampling_params=self._sampling_params)
            
            # 提取响应文本
            response = outputs[0].outputs[0].text
            return response
        except Exception as e:
            raise RuntimeError(f"vLLM模型生成失败: {str(e)}")


class OpenAILLM(BaseLLM):
    """OpenAI LLM实现"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo", base_url: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self._client = None
    
    def _get_client(self):
        """延迟加载OpenAI客户端"""
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except ImportError:
                raise ImportError("请安装openai库: pip install openai")
        return self._client
    
    def is_available(self) -> bool:
        """检查OpenAI是否可用"""
        if not self.api_key:
            return False
        try:
            import openai
            return True
        except ImportError:
            return False
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """使用OpenAI生成文本"""
        if not self.is_available():
            raise ValueError("OpenAI API key未配置或openai库未安装")
        
        client = self._get_client()
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的Linux内核问题分析专家，擅长从技术文章中提取结构化的问题案例信息。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API调用失败: {str(e)}")


class DeepSeekLLM(BaseLLM):
    """DeepSeek LLM实现（兼容OpenAI接口）"""
    
    def __init__(self, api_key: str = None, model: str = "deepseek-chat"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.model = model
        self.base_url = "https://api.deepseek.com/v1"
        self._client = None
    
    def _get_client(self):
        """延迟加载客户端"""
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except ImportError:
                raise ImportError("请安装openai库: pip install openai")
        return self._client
    
    def is_available(self) -> bool:
        """检查DeepSeek是否可用"""
        if not self.api_key:
            return False
        try:
            import openai
            return True
        except ImportError:
            return False
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """使用DeepSeek生成文本"""
        if not self.is_available():
            raise ValueError("DeepSeek API key未配置或openai库未安装")
        
        client = self._get_client()
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的Linux内核问题分析专家，擅长从技术文章中提取结构化的问题案例信息。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"DeepSeek API调用失败: {str(e)}")


class MockLLM(BaseLLM):
    """Mock LLM用于测试（不调用真实API）"""
    
    def is_available(self) -> bool:
        return True
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """返回模拟的结构化数据"""
        return json.dumps({
            "title": "Linux内核问题案例（模拟数据）",
            "phenomenon": "系统出现内核panic错误（模拟数据）",
            "environment": "Linux 5.10.0（模拟数据）",
            "root_cause": "内存损坏导致内核panic（模拟数据）",
            "troubleshooting_steps": ["步骤1", "步骤2"],
            "solution": "修复内存问题（模拟数据）",
            "key_logs": "kernel panic日志（模拟数据）",
            "analysis_process": "分析过程（模拟数据）"
        }, ensure_ascii=False)


class LLMFactory:
    """LLM工厂类"""
    
    @staticmethod
    def create_llm(llm_type: str = "auto", **kwargs) -> BaseLLM:
        """
        创建LLM实例
        
        Args:
            llm_type: LLM类型
                - "auto": 自动选择（优先本地模型）
                - "ollama": Ollama本地模型（推荐）
                - "vllm": vLLM本地模型（高性能）
                - "qwen": Qwen本地模型（Transformers）
                - "chatglm": ChatGLM本地模型
                - "openai": OpenAI API（付费）
                - "deepseek": DeepSeek API（付费）
                - "mock": Mock模式（测试用）
            **kwargs: 传递给LLM构造函数的参数
            
        Returns:
            LLM实例
        """
        if llm_type == "auto":
            # 自动选择：优先本地免费模型
            # 1. 优先尝试Ollama（最简单，推荐）
            ollama = OllamaLLM(**kwargs)
            if ollama.is_available():
                print(f"✓ 使用Ollama本地模型: {ollama.model}")
                return ollama
            
            # 2. 尝试vLLM（高性能）
            vllm = VLLMLocalLLM(**kwargs)
            if vllm.is_available():
                print("✓ 使用vLLM本地模型")
                return vllm
            
            # 3. 尝试Qwen本地模型
            qwen = QwenLocalLLM(**kwargs)
            if qwen.is_available():
                print("✓ 使用Qwen本地模型")
                return qwen
            
            # 4. 尝试ChatGLM本地模型
            chatglm = ChatGLMLocalLLM(**kwargs)
            if chatglm.is_available():
                print("✓ 使用ChatGLM本地模型")
                return chatglm
            
            # 5. 最后尝试云端API（付费）
            deepseek = DeepSeekLLM(**kwargs)
            if deepseek.is_available():
                print("✓ 使用DeepSeek API（付费）")
                return deepseek
            
            openai_llm = OpenAILLM(**kwargs)
            if openai_llm.is_available():
                print("✓ 使用OpenAI API（付费）")
                return openai_llm
            
            # 6. 如果都没有，使用Mock
            print("⚠ 警告: 没有可用的LLM，使用Mock模式")
            print("\n推荐安装方式:")
            print("  方式1（推荐）: 安装Ollama并下载模型")
            print("    1. 访问 https://ollama.ai/ 下载安装Ollama")
            print("    2. 运行: ollama pull qwen:1.8b")
            print("    3. 运行: ollama serve")
            print("  方式2: 安装vLLM（高性能）")
            print("    pip install vllm")
            print("  方式3: 安装Transformers")
            print("    pip install transformers torch accelerate")
            return MockLLM()
        
        elif llm_type == "ollama":
            return OllamaLLM(**kwargs)
        elif llm_type == "vllm":
            return VLLMLocalLLM(**kwargs)
        elif llm_type == "qwen":
            return QwenLocalLLM(**kwargs)
        elif llm_type == "chatglm":
            return ChatGLMLocalLLM(**kwargs)
        elif llm_type == "openai":
            return OpenAILLM(**kwargs)
        elif llm_type == "deepseek":
            return DeepSeekLLM(**kwargs)
        elif llm_type == "mock":
            return MockLLM(**kwargs)
        else:
            raise ValueError(f"不支持的LLM类型: {llm_type}")


# 创建全局LLM实例
llm_instance = None


def get_llm(llm_type: str = "auto", **kwargs) -> BaseLLM:
    """获取LLM实例（单例模式）"""
    global llm_instance
    if llm_instance is None:
        llm_instance = LLMFactory.create_llm(llm_type, **kwargs)
    return llm_instance