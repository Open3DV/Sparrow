import os
import cv2
import numpy as np
from numpy import sqrt, arctan2, pi, sin, cos, abs
import matplotlib.pyplot as plt
from triangulation import triangulation


def read_calib_param(param_txt):
    with open(param_txt, 'r') as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]
    intrinsic_1 = np.array([[float(lines[0]), float(lines[1]), float(lines[2])],
                            [float(lines[3]), float(lines[4]), float(lines[5])],
                            [float(lines[6]), float(lines[7]), float(lines[8])]])
    kc1 = np.array([float(lines[9]),
                    float(lines[10]),
                    float(lines[11]),
                    float(lines[12]),
                    float(lines[13])])
    intrinsic_2 = np.array([[float(lines[14]), float(lines[15]), float(lines[16])],
                            [float(lines[17]), float(lines[18]), float(lines[19])],
                            [float(lines[20]), float(lines[21]), float(lines[22])]])
    kc2 = np.array([float(lines[23]),
                    float(lines[24]),
                    float(lines[25]),
                    float(lines[26]),
                    float(lines[27])])
    R = np.array([[float(lines[28]), float(lines[29]), float(lines[30])],
                  [float(lines[31]), float(lines[32]), float(lines[33])],
                  [float(lines[34]), float(lines[35]), float(lines[36])]])
    T = np.array([[float(lines[37])],
                  [float(lines[38])],
                  [float(lines[39])]])

    return intrinsic_1, kc1, intrinsic_2, kc2, R, T


def phase_shift_4(phases):
    a = phases[3].astype(np.int16) - phases[1].astype(np.int16)
    b = phases[0].astype(np.int16) - phases[2].astype(np.int16)

    thresh = 10

    r = sqrt(a * a + b * b) + 0.5
    phase = pi + arctan2(a, b)
    mask = r >= thresh
    return phase, mask


def phase_shift_6(phases):
    b = phases[3] * sin(0 * 2 * pi / 6.0) \
        + phases[4] * sin(1 * 2 * pi / 6.0) \
        + phases[5] * sin(2 * 2 * pi / 6.0) \
        + phases[0] * sin(3 * 2 * pi / 6.0) \
        + phases[1] * sin(4 * 2 * pi / 6.0) \
        + phases[2] * sin(5 * 2 * pi / 6.0)

    a = phases[3] * cos(0 * 2 * pi / 6.0) \
        + phases[4] * cos(1 * 2 * pi / 6.0) \
        + phases[5] * cos(2 * 2 * pi / 6.0) \
        + phases[0] * cos(3 * 2 * pi / 6.0) \
        + phases[1] * cos(4 * 2 * pi / 6.0) \
        + phases[2] * cos(5 * 2 * pi / 6.0)

    # saturate_mask = (phases[0]==255 | phases[1]==255 | phases[2]==255 | phases[3]==255 | phases[4]==255 | phases[5]==255)
    thresh = 10

    r = sqrt(a * a + b * b) + 0.5
    phase = pi + arctan2(a, b)
    mask = r >= thresh
    return phase, mask


def phase_unwrap(last_phase, next_phase, scale_factor):
    predicted_phase = last_phase * scale_factor
    nth_period = (predicted_phase - next_phase) / (2 * pi)
    k = nth_period.round()
    corrected_phase = 2 * pi * k + next_phase
    corrected_phase[next_phase == -1] = -1
    error = abs(corrected_phase - predicted_phase)
    return corrected_phase


def read_phases(phase_dir):
    phases = []
    for i in range(36):
        phase = cv2.imread(os.path.join(phase_dir, 'phase%02d.bmp' % i), 0)
        phases.append(phase)
    return phases


def show_pseudo_color_phase(phase, save_file='result.png'):
    max_value = np.max(phase)
    min_value = np.min(phase)
    phase_color = (phase - min_value) / (max_value - min_value) * 255
    phase_color = phase_color.astype(np.uint8)
    phase_color = cv2.applyColorMap(phase_color, cv2.COLORMAP_JET)
    phase_color[phase < 0] = [0, 0, 0]
    cv2.imwrite(save_file, phase_color)
    cv2.namedWindow('phase', 0)
    cv2.imshow('phase', phase_color)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def show_phases(phases):
    for i in range(len(phases)):
        cv2.imshow('phase%d' % i, phases[i])
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def get_phase(phases):
    phase1, mask1 = phase_shift_4(phases[0:4])
    show_pseudo_color_phase(phase1, 'result1.png')
    phase2, mask2 = phase_shift_4(phases[4:8])
    show_pseudo_color_phase(phase2, 'result2.png')
    phase_wrapped = phase_unwrap(last_phase=phase1, next_phase=phase2, scale_factor=8)

    phase3, mask3 = phase_shift_4(phases[8:12])
    show_pseudo_color_phase(phase3, 'result3.png')
    phase_wrapped = phase_unwrap(last_phase=phase_wrapped, next_phase=phase3, scale_factor=4)

    phase4, mask4 = phase_shift_6(phases[12:18])
    show_pseudo_color_phase(phase4, 'result4.png')
    phase_wrapped = phase_unwrap(last_phase=phase_wrapped, next_phase=phase4, scale_factor=4)

    mask = mask1 & mask2 & mask3 & mask4

    return phase_wrapped, mask


def get_DMD_coordinate(phases):
    phase, mask = get_phase(phases)
    DMD_coordinate = phase / (2 * pi) * 10
    return DMD_coordinate, mask


def reconstruct(params_path, raw_phase_dir, output_path):
    left_intrinsic, kc_left, right_intrinsic, kc_right, R, T = read_calib_param(params_path)

    phases = read_phases(raw_phase_dir)
    print(phases)
    DMD_x, mask_x = get_DMD_coordinate(phases[0:18])
    DMD_y, mask_y = get_DMD_coordinate(phases[18:36])
    print('mask', mask_x, mask_y)
    mask = mask_x & mask_y

    xR = np.array(list(zip(DMD_x[mask], DMD_y[mask])), dtype=np.float32)
    X, Y = np.meshgrid(np.arange(0, 1920), np.arange(0, 1200))

    print(X.shape,Y.shape,mask.shape)
    print(mask)
    print(X[mask], Y[mask])

    xL = np.array(list(zip(X[mask], Y[mask])), dtype=np.float32)
    print(xL.shape)

    XL, XR, ERR = triangulation(xL, xR,
                                R, T,
                                left_intrinsic, kc_left, 0,
                                right_intrinsic, kc_right, 0)

    np.savetxt(output_path, XL, fmt='%.4f', delimiter=',', newline='\n')


if __name__ == '__main__':
    reconstruct('param.txt', 'capture', 'point_cloud.xyz')
