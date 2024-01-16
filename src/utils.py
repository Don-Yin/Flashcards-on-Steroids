def stripe_each_line(str):
    lines = str.split("\n")
    striped_lines = [line.strip() for line in lines]
    striped_lines = [line if line else "\n" for line in striped_lines]
    return "\n".join(striped_lines)
