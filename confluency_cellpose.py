"""
Cell Confluency Calculator using Cellpose

This script takes an image, applies CLAHE preprocessing, calculates the cell 
probability map using Cellpose, applies thresholding to create a binary mask 
(live cells vs background/contaminants), and calculates the cell confluency 
(percentage of image area covered by cells).

Based on Cellpose's multi-stage filtering approach:
1. Semantic Rejection: The network assigns low probability logits to texture-mismatched debris
2. Topological Rejection: flow consistency check discards objects without coherent center-seeking flows
3. Morphological Rejection: min_size parameter eliminates small components

The cell probability map (cellprob) is a logit value where:
- Logit > 0: High confidence cell (probability > 0.5)
- Logit < 0: High confidence background (probability < 0.5)
- Logit = 0: 50% probability threshold
"""

import os
import sys
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from cellpose import models, io

# Import CLAHE function from the local module
from CLAHE import apply_clahe


def sigmoid(x):
    """
    Convert logits to probabilities using the sigmoid function.
    
    p = 1 / (1 + exp(-x))
    
    - Logit 0 → 0.5 (50% probability)
    - Logit +6 → ~0.9975 (high confidence cell)
    - Logit -6 → ~0.0025 (high confidence background)
    """
    return 1 / (1 + np.exp(-np.clip(x, -500, 500)))


def get_probability_map(cellprob_logits):
    """
    Convert the cell probability logit map to actual probabilities (0-1 range).
    
    Args:
        cellprob_logits: Raw cell probability output from Cellpose (logits)
    
    Returns:
        Probability map with values in [0, 1] range
    """
    return sigmoid(cellprob_logits)


def apply_clahe_to_image(img, clip_limit=2.0, tile_grid_size=(8, 8)):
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to an image.
    
    Args:
        img: Input image (grayscale or RGB)
        clip_limit: Threshold for contrast limiting
        tile_grid_size: Size of grid for histogram equalization
    
    Returns:
        CLAHE-enhanced grayscale image
    """
    # Convert to grayscale if needed
    if img.ndim == 3:
        img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        img_gray = img
    
    # Create CLAHE object and apply
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    img_clahe = clahe.apply(img_gray)
    
    return img_clahe


def calculate_confluency(
    image_path: str,
    model_name: str = 'cpsam',
    diameter: float = 50,
    flow_threshold: float = 2.0,
    cellprob_threshold: float = -1,
    niter: int = 2000,
    use_gpu: bool = True,
    save_outputs: bool = True,
    output_dir: str = None,
    clahe_clip_limit: float = 2.0,
    clahe_tile_grid_size: tuple = (8, 8)
) -> dict:
    """
    Calculate cell confluency from an image using Cellpose.
    Outputs visualization images at each processing step.
    
    The confluency is calculated by:
    1. Running CLAHE preprocessing to enhance contrast
    2. Running Cellpose to get the cell probability map
    3. Applying probability threshold to create binary mask
    4. Calculating the percentage of the image covered by cells
    
    Args:
        image_path: Path to the input image
        model_name: Cellpose model to use ('cyto', 'cyto2', 'nuclei', 'cpsam', etc.)
        diameter: Expected cell diameter in pixels
        flow_threshold: Flow error threshold for rejecting bad masks (default 2.0)
        cellprob_threshold: Cell probability threshold (default -1)
        niter: Number of iterations for flow dynamics (default 2000)
        use_gpu: Whether to use GPU acceleration
        save_outputs: Whether to save output images
        output_dir: Directory to save outputs (defaults to image directory)
        clahe_clip_limit: CLAHE clip limit (default 2.0)
        clahe_tile_grid_size: CLAHE tile grid size (default (8, 8))
    
    Returns:
        dict containing confluency results and intermediate outputs
    """
    
    # Setup output directory
    if output_dir is None:
        output_dir = os.path.dirname(image_path)
    if output_dir == '':
        output_dir = '.'
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    
    # =========================================================================
    # STEP 1: Load and display original image
    # =========================================================================
    print(f"\n{'='*60}")
    print("STEP 1: Loading Original Image")
    print(f"{'='*60}")
    
    img = io.imread(image_path)
    print(f"Loaded image: {image_path}")
    
    # Get image dimensions
    if img.ndim == 2:
        height, width = img.shape
        channels = 1
    elif img.ndim == 3:
        height, width, channels = img.shape
    else:
        raise ValueError(f"Unexpected image dimensions: {img.ndim}")
    
    total_pixels = height * width
    print(f"Image size: {width}x{height} ({channels} channel{'s' if channels > 1 else ''})")
    
    # Store original for visualization
    img_original = img.copy()
    
    # =========================================================================
    # STEP 2: Apply CLAHE preprocessing
    # =========================================================================
    print(f"\n{'='*60}")
    print("STEP 2: Applying CLAHE Preprocessing")
    print(f"{'='*60}")
    
    img_clahe = apply_clahe_to_image(img, clahe_clip_limit, clahe_tile_grid_size)
    print(f"CLAHE parameters: clip_limit={clahe_clip_limit}, tile_grid_size={clahe_tile_grid_size}")
    print("CLAHE preprocessing complete")
    
    # Use CLAHE-processed image for Cellpose
    img = img_clahe
    
    # =========================================================================
    # STEP 3: Run Cellpose and get Cell Probability Map
    # =========================================================================
    print(f"\n{'='*60}")
    print("STEP 3: Computing Cell Probability Map")
    print(f"{'='*60}")
    
    print(f"Loading Cellpose model: {model_name}")
    model = models.CellposeModel(gpu=use_gpu, pretrained_model=model_name)
    
    print("Running Cellpose segmentation...")
    masks, flows, styles = model.eval(
        img,
        diameter=diameter,
        flow_threshold=flow_threshold,
        cellprob_threshold=cellprob_threshold,
        niter=niter
    )
    
    # Extract cell probability map (logits)
    cellprob_map = flows[2]
    
    # Convert to probability (0-1 range) for visualization
    probability_map = get_probability_map(cellprob_map)
    
    print(f"Cell probability map stats (logits):")
    print(f"  Min: {cellprob_map.min():.3f}")
    print(f"  Max: {cellprob_map.max():.3f}")
    print(f"  Mean: {cellprob_map.mean():.3f}")
    
    # =========================================================================
    # STEP 4: Apply threshold to create Binary Mask
    # =========================================================================
    print(f"\n{'='*60}")
    print("STEP 4: Creating Binary Mask (Cells vs Background)")
    print(f"{'='*60}")
    
    # Apply threshold to logits
    binary_mask = cellprob_map > cellprob_threshold
    
    # Calculate cell area
    cell_area_pixels = np.sum(binary_mask)
    confluency = (cell_area_pixels / total_pixels) * 100
    
    print(f"Threshold applied: {cellprob_threshold} (logit)")
    print(f"Equivalent probability: {sigmoid(cellprob_threshold):.2%}")
    print(f"Cell pixels: {cell_area_pixels:,} / {total_pixels:,}")
    print(f"Confluency: {confluency:.2f}%")
    
    # =========================================================================
    # FINAL: Create side-by-side comparison of all steps
    # =========================================================================
    print(f"\n{'='*60}")
    print("FINAL: Creating Process Visualization")
    print(f"{'='*60}")
    
    if save_outputs:
        final_path = os.path.join(output_dir, f"{base_name}_cellpose_overview.png")
        
        # Create 2x2 layout for the 4 steps
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        
        # Step 1: Original Image
        ax1 = axes[0, 0]
        if img_original.ndim == 2:
            ax1.imshow(img_original, cmap='gray')
        else:
            ax1.imshow(img_original)
        ax1.set_title('Step 1: Original Image', fontsize=12, fontweight='bold', pad=10)
        ax1.axis('off')
        
        # Step 2: CLAHE Enhanced
        ax2 = axes[0, 1]
        ax2.imshow(img_clahe, cmap='gray')
        ax2.set_title('Step 2: CLAHE Enhanced', fontsize=12, fontweight='bold', pad=10)
        ax2.axis('off')
        
        # Step 3: Probability Map
        ax3 = axes[1, 0]
        im3 = ax3.imshow(probability_map, cmap='RdYlGn', vmin=0, vmax=1)
        ax3.set_title('Step 3: Cell Probability Map', fontsize=12, fontweight='bold', pad=10)
        ax3.axis('off')
        cbar3 = plt.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04)
        cbar3.set_label('Probability', fontsize=10)
        
        # Step 4: Binary Mask
        ax4 = axes[1, 1]
        cmap_binary = LinearSegmentedColormap.from_list('binary_cells', ['black', '#00FF00'])
        ax4.imshow(binary_mask, cmap=cmap_binary)
        ax4.set_title(f'Step 4: Binary Mask\nConfluency: {confluency:.1f}%', 
                      fontsize=12, fontweight='bold', pad=10)
        ax4.axis('off')
        
        # Add overall title with results
        fig.suptitle(f'Cell Confluency Analysis Pipeline\n'
                     f'Model: {model_name} | Diameter: {diameter} | '
                     f'Threshold: {cellprob_threshold}',
                     fontsize=14, fontweight='bold', y=0.98)
        
        plt.tight_layout()
        plt.savefig(final_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f"Saved: {final_path}")
    
    # Print final summary
    print(f"\n{'='*60}")
    print("CONFLUENCY ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"Cell probability threshold: {cellprob_threshold}")
    print(f"Total image area: {total_pixels:,} pixels")
    print(f"Cell area: {cell_area_pixels:,} pixels")
    print(f"Cell confluency: {confluency:.2f}%")
    print(f"{'='*60}\n")
    
    return {
        'confluency': confluency,
        'cell_area_pixels': int(cell_area_pixels),
        'total_area_pixels': int(total_pixels),
        'cellprob_map': cellprob_map,
        'probability_map': probability_map,
        'binary_mask': binary_mask,
        'masks': masks
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Calculate cell confluency from an image using Cellpose'
    )
    parser.add_argument(
        'image_path',
        type=str,
        help='Path to the input image'
    )
    parser.add_argument(
        '--model', '-m',
        type=str,
        default='cpsam',
        help='Cellpose model to use (default: cpsam)'
    )
    parser.add_argument(
        '--diameter', '-d',
        type=float,
        default=50,
        help='Expected cell diameter in pixels (default: 50)'
    )
    parser.add_argument(
        '--flow_threshold', '-ft',
        type=float,
        default=2.0,
        help='Flow error threshold (default: 2.0)'
    )
    parser.add_argument(
        '--cellprob_threshold', '-ct',
        type=float,
        default=-1,
        help='Cell probability threshold (default: -1)'
    )
    parser.add_argument(
        '--niter',
        type=int,
        default=2000,
        help='Number of flow dynamics iterations (default: 2000)'
    )
    parser.add_argument(
        '--clahe_clip',
        type=float,
        default=2.0,
        help='CLAHE clip limit (default: 2.0)'
    )
    parser.add_argument(
        '--output_dir', '-o',
        type=str,
        default=None,
        help='Output directory for results (default: same as input image)'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save output files'
    )
    parser.add_argument(
        '--cpu',
        action='store_true',
        help='Use CPU instead of GPU'
    )
    
    args = parser.parse_args()
    
    # Validate input
    if not os.path.exists(args.image_path):
        print(f"Error: Image file not found: {args.image_path}")
        sys.exit(1)
    
    # Run confluency calculation
    results = calculate_confluency(
        image_path=args.image_path,
        model_name=args.model,
        diameter=args.diameter,
        flow_threshold=args.flow_threshold,
        cellprob_threshold=args.cellprob_threshold,
        niter=args.niter,
        use_gpu=not args.cpu,
        save_outputs=not args.no_save,
        output_dir=args.output_dir,
        clahe_clip_limit=args.clahe_clip
    )
    
    print(f"\n{'#'*60}")
    print(f"FINAL CONFLUENCY: {results['confluency']:.2f}%")
    print(f"{'#'*60}")
