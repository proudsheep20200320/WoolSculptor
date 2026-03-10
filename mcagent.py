import time
import numpy as np
import open3d as o3d
from mcpi.minecraft import Minecraft
import os
import shutil

# .ply generator
from text_to_3d import generate_ply_from_text

# ================= PLAETTE =================
SCALE = 15  # scale
SHAPE_PREFIX = "outputs/my_model"
PLY_FILE = "outputs/my_model/shap_e_mesh_0.ply" # path of the generated point cloud file

# (RGB -> wool block color mapping)
PALETTE = [
    ((240, 240, 240), 35, 0),  # 白色
    ((240, 120, 20), 35, 1),   # 橙色
    ((200, 80, 200), 35, 2),   # 品红
    ((100, 150, 240), 35, 3),  # 浅蓝
    ((240, 200, 20), 35, 4),   # 黄色
    ((100, 200, 50), 35, 5),   # 黄绿色
    ((240, 150, 180), 35, 6),  # 粉红
    ((100, 100, 100), 35, 7),  # 灰色
    ((200, 200, 200), 35, 8),  # 淡灰
    ((40, 100, 150), 35, 9),   # 青色
    ((120, 50, 180), 35, 10),  # 紫色
    ((40, 40, 180), 35, 11),   # 蓝色
    ((100, 60, 30), 35, 12),   # 棕色
    ((40, 100, 40), 35, 13),   # 绿色
    ((180, 40, 40), 35, 14),   # 红色
    ((20, 20, 20), 35, 15),    # 黑色
]

def get_closest_block(rgb):
    """match color"""
    min_dist = float('inf')
    best_block = (35, 0)
    for p_color, b_id, b_data in PALETTE:
        dist = (rgb[0]-p_color[0])**2 + (rgb[1]-p_color[1])**2 + (rgb[2]-p_color[2])**2
        if dist < min_dist:
            min_dist = dist
            best_block = (b_id, b_data)
    return best_block

def build_from_ply(mc, player_pos):
    """build the object"""
    pcd = o3d.io.read_point_cloud(PLY_FILE)
    points = np.asarray(pcd.points)
    colors = np.asarray(pcd.colors) * 255.0 

    scaled_points = np.round(points * SCALE).astype(int)
    voxel_dict = {}
    for i in range(len(scaled_points)):
        pos = tuple(scaled_points[i])
        color = colors[i]
        if pos not in voxel_dict:
            voxel_dict[pos] = [color]
        else:
            voxel_dict[pos].append(color)

    min_y = min([pos[2] for pos in voxel_dict.keys()]) # the sea level
    
    count = 0
    for pos, c_list in voxel_dict.items():
        avg_color = np.mean(c_list, axis=0)
        b_id, b_data = get_closest_block(avg_color)

        # 10 voxels forward
        mc_x = player_pos.x + pos[0] + 10
        mc_y = player_pos.y + (pos[2] - min_y) 
        mc_z = player_pos.z + pos[1] 

        mc.setBlock(mc_x, mc_y, mc_z, b_id, b_data)
        count += 1
    return count

# ================= THE MAIN LOOP =================
def main():
    print("connecting Minecraft...")
    try:
        mc = Minecraft.create("127.0.0.1", 4711)
        mc.postToChat("§a[AI Agent] coming！print '!build <object>' to build your wool crafts")
        print("listenning")
    except Exception as e:
        print(f"failed to connect: {e}")
        return

    while True:
        # 抓取自上次轮询以来的所有聊天记录
        chats = mc.events.pollChatPosts()
        
        for chat in chats:
            msg = chat.message.strip()
            
            # triggered by '!build '
            if msg.startswith("!build "):
                prompt = msg[7:].strip()
                mc.postToChat(f"§e[AI Agent] recieved！imagining:{prompt}")
                print(f"start generating: {prompt}")
                player_pos = mc.entity.getTilePos(chat.entityId)
                try:
                    if os.path.exists(PLY_FILE):
                        os.remove(PLY_FILE) # remove the establisted file
                    generate_ply_from_text(prompt, SHAPE_PREFIX)
                    mc.postToChat("§e[AI Agent] 3D model generated successfully, start building...")
                    
                    # placing blocks
                    blocks_count = build_from_ply(mc, player_pos)
                    mc.postToChat(f"§a[AI Agent] established!{blocks_count} blocks used, enjoy!")
                    
                except Exception as e:
                    mc.postToChat(f"§c[AI Agent] error: {e}")
                    print(f"error: {e}")
                    
        time.sleep(2)

if __name__ == "__main__":
    main()