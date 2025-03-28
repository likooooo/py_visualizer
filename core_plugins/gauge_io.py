def parse_line(line):
    # 按制表符分割行
    items = line.strip().split('\t')
    
    # 转换每个字段到合适的类型
    converted = []
    for item in items:
        # 尝试转换为int
        try:
            converted.append(int(item))
            continue
        except ValueError:
            pass
        
        # 尝试转换为float
        try:
            converted.append(float(item))
            continue
        except ValueError:
            pass
        
        # 保持字符串不变
        converted.append(item if item != 'NA' else None)
    
    return tuple(converted)

# 示例使用
line = "1\tL48P110\t1\t1\t9245770\t87078000\t9246230\t87078000\t0\t48\t110\t57.51\t58.156726\t-1\t-1\t2.5\t200\t1.5\t-1\t-1\tLS\tNA"
data = [parse_line(line)]  # 对于多行文件，可以循环调用parse_line

print(data)