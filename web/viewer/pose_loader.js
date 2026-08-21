/** Load and validate an imported viewer pose document. No pose data is created. */

export const POSE_SCHEMA_VERSION = 1;

export class PoseValidationError extends Error {
    constructor(message, details = []) {
        super(message);
        this.name = 'PoseValidationError';
        this.details = details;
    }
}

const REQUIRED_FRAME_FIELDS = [
    'thorax',
    'orientation',
    'COM',
    'joint_angles',
    'joint_velocities',
    'contacts',
    'trajectory',
];

export function validatePoseDocument(document) {
    const errors = [];
    if (!document || typeof document !== 'object' || Array.isArray(document)) {
        throw new PoseValidationError('Pose document must be an object.');
    }
    if (!document.metadata || typeof document.metadata !== 'object') errors.push('metadata');
    if (!Number.isFinite(document.fps) || document.fps <= 0) errors.push('fps');
    if (!Number.isInteger(document.frame_count) || document.frame_count < 0) errors.push('frame_count');
    if (!document.mesh || typeof document.mesh !== 'object') errors.push('mesh');
    else {
        ['renderer', 'render_mode', 'scientific_mesh', 'visibility'].forEach((field) => {
            if (!(field in document.mesh)) errors.push(`mesh.${field}`);
        });
    }
    if (!Array.isArray(document.frames)) errors.push('frames');
    if (Array.isArray(document.frames) && document.frames.length !== document.frame_count) {
        errors.push('frames.length must equal frame_count');
    }
    if (Array.isArray(document.frames)) {
        document.frames.forEach((frame, index) => {
            if (!frame || typeof frame !== 'object' || Array.isArray(frame)) {
                errors.push(`frames[${index}]`);
                return;
            }
            REQUIRED_FRAME_FIELDS.forEach((field) => {
                if (!(field in frame)) errors.push(`frames[${index}].${field}`);
            });
        });
    }
    if (errors.length) throw new PoseValidationError('Invalid viewer pose document.', errors);
    return document;
}

export async function loadPoseJSON(input) {
    let document = input;
    if (typeof input === 'string') document = JSON.parse(input);
    else if (input && typeof input.text === 'function') document = JSON.parse(await input.text());
    return validatePoseDocument(document);
}
