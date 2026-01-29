
import os
import sys
import cv2
import numpy as np
import matplotlib.pyplot as plt
from cellpose import models
from matplotlib.colors import LinearSegmentedColormap

# Import local modules
sys.path.append(os.getcwd())

def visualize_grid_sweep(image_path, grid_sizes, output_path):
    print(f"Processing {image_path}...")
    
    # Setup plot
    num_plots = len(grid_sizes)
    cols = 3
    rows = (num_plots + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(18, 5 * rows))
    axes = axes.flatten()
    
    # Load original image once
    img_orig = cv2.imread(image_path)
    if img_orig is None:
        print(f"Error: Could not read image at {image_path}")
        return

    # Convert to grayscale for CLAHE
    img_gray = cv2.cvtColor(img_orig, cv2.COLOR_BGR2GRAY)
    
    # Load model
    print("Loading Cellpose model...")
    model = models.CellposeModel(gpu=True, pretrained_model='cpsam')
    
    fixed_clip_limit = 2.0
    
    for i, gs in enumerate(grid_sizes):
        print(f"  Running for Grid Size: {gs}x{gs}...")
        ax = axes[i]
        
        # 1. Apply CLAHE with fixed Clip Limit and varying Grid Size
        clahe = cv2.createCLAHE(clipLimit=fixed_clip_limit, tileGridSize=(gs, gs))
        img_clahe = clahe.apply(img_gray)
        
        # 2. Run Cellpose
        masks, flows, styles = model.eval(
            img_clahe,
            diameter=50,
            flow_threshold=2.0,
            cellprob_threshold=-1,
            niter=2000
        )
        
        cellprob_map = flows[2]
        binary_mask = cellprob_map > -1
        confluency = (np.sum(binary_mask) / binary_mask.size) * 100
        
        # 3. Visualize
        ax.imshow(img_clahe, cmap='gray')
        
        # Overlay Mask (Green with transparency)
        cmap_mask = LinearSegmentedColormap.from_list('alpha_green', [(0, 0, 0, 0), (0, 1, 0, 0.4)])
        ax.imshow(binary_mask, cmap=cmap_mask)
        
        ax.set_title(f"Grid Size: {gs}x{gs} | Confluency: {confluency:.1f}%", fontsize=14, fontweight='bold')
        ax.axis('off')

    # Turn off unused subplots
    for j in range(i + 1, len(axes)):
        axes[j].axis('off')

    plt.suptitle(f"Grid Size Sweep (Fixed Clip Limit = {fixed_clip_limit})", fontsize=16, fontweight='bold', y=0.99)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Comparison saved to {output_path}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualize CLAHE Grid Size sweep')
    parser.add_argument('image_path', help='Path to input image')
    args = parser.parse_args()
    
    target_image = args.image_path
    
    # Generate output filename based on input
    dirname = os.path.dirname(target_image)
    basename = os.path.splitext(os.path.basename(target_image))[0]
    output_file = os.path.join(dirname, f"gridsize_sweep_{basename}.png")
    
    # Grid sizes to test: 2, 4, 8, 12, 16, 32
    grid_sizes = [2, 4, 8, 12, 16, 32]
    
    if os.path.exists(target_image):
        visualize_grid_sweep(target_image, grid_sizes, output_file)
    else:
        print(f"Error: File not found: {target_image}")
