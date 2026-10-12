"""
增强版聊天界面 - 带语义搜索功能
使用火山引擎大模型 + 硅基流动BAAI/bge-m3语义搜索
"""

import os
import sys
from datetime import datetime

def main():
    print("=" * 60)
    print("      关系动力学对话助手（增强版）")
    print("      火山引擎大模型 + 语义搜索")
    print("=" * 60)
    
    # 检查火山引擎API密钥
    ark_api_key = os.environ.get("ARK_API_KEY")
    if not ark_api_key:
        ark_api_key = input("\n请输入火山引擎 API Key: ").strip()
    
    # 检查硅基流动API密钥
    siliconflow_api_key = os.environ.get("SILICONFLOW_API_KEY")
    if not siliconflow_api_key:
        siliconflow_api_key = input("\n请输入硅基流动 API Key (用于语义搜索): ").strip()
        if siliconflow_api_key:
            os.environ["SILICONFLOW_API_KEY"] = siliconflow_api_key
    
    # 是否启用深度思考
    print("\n是否启用深度思考模式？")
    print("  y: 启用（适合复杂问题分析，响应时间较长）")
    print("  n: 不启用（默认，快速响应）")
    
    while True:
        choice = input("请输入选择 (y/n): ").strip().lower()
        if choice == 'y':
            thinking_enabled = True
            print("✓ 深度思考模式已启用")
            break
        elif choice in ['n', '']:
            thinking_enabled = False
            print("深度思考模式未启用")
            break
        else:
            print("请输入 y 或 n")
    
    # 初始化增强版对话系统
    try:
        from cn_llm_integration import ArkDialogueSystem
        
        print("\n初始化对话系统...")
        dialogue_system = ArkDialogueSystem(
            api_key=ark_api_key,
            thinking_enabled=thinking_enabled
        )
        
        # 检查语义搜索功能
        if siliconflow_api_key:
            print("✓ 语义搜索功能已启用")
            print("✓ 关系动力学理论将被动态检索并注入")
        else:
            print("⚠️ 语义搜索功能不可用（未设置硅基流动API密钥）")
        
        print("\n" + "=" * 60)
        print("对话助手：您好！我是基于关系动力学理论的对话助手。")
        print("请描述您遇到的人际关系问题，我会陪伴您一起思考。")
        print("(输入 'quit' 或 'exit' 结束对话)")
        if thinking_enabled:
            print("(深度思考模式已启用，回复可能需要较长时间)")
        print("=" * 60 + "\n")
        
        # 对话记录
        conversation_log = []
        
        # 主循环
        while True:
            user_input = input("你：").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit", "退出"]:
                print("\n对话助手：感谢您的信任，祝您一切顺利！")
                
                # 保存对话记录
                if conversation_log:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"对话记录_{timestamp}.txt"
                    
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write("=" * 60 + "\n")
                        f.write("关系动力学对话记录\n")
                        f.write(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"深度思考模式：{'启用' if thinking_enabled else '未启用'}\n")
                        f.write("=" * 60 + "\n\n")
                        
                        for role, message in conversation_log:
                            f.write(f"{role}：{message}\n\n")
                    
                    print(f"✓ 对话记录已保存到：{filename}")
                
                break
            
            # 记录用户输入
            conversation_log.append(("用户", user_input))
            
            # 生成回复
            response = dialogue_system.respond(user_input)
            
            # 显示回复
            print(f"\n对话助手：{response}\n")
            
            # 记录助手回复
            conversation_log.append(("对话助手", response))
        
    except Exception as e:
        print(f"\n❌ 初始化失败：{str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
