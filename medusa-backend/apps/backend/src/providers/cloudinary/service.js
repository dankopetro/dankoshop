"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@medusajs/framework/utils");
const cloudinary_1 = require("cloudinary");
const stream_1 = require("stream");
const uuid_1 = require("uuid");
class CloudinaryFileProviderService extends utils_1.AbstractFileProviderService {
    constructor({ logger }, options) {
        super();
        this.logger_ = logger;
        this.options_ = options;
        cloudinary_1.v2.config({
            cloud_name: options.cloudName,
            api_key: options.apiKey,
            api_secret: options.apiSecret,
            secure: options.secure ?? true,
        });
    }
    static validateOptions(options) {
        if (!options.apiKey || !options.apiSecret || !options.cloudName) {
            throw new utils_1.MedusaError(utils_1.MedusaError.Types.INVALID_DATA, "API key, API secret or Cloud Name is required in the cloudinary provider's options.");
        }
    }
    async upload(file) {
        const publicId = this.generatePublicId(file.filename);
        console.log({ publicId });
        // Decode file content properly (handle base64 and binary)
        let buffer;
        const decodedBase64 = Buffer.from(file.content, "base64");
        if (decodedBase64.toString("base64") === file.content) {
            buffer = decodedBase64;
        } else {
            buffer = Buffer.from(file.content, "binary");
        }
        // Detect resource type from file extension
        const ext = file.filename?.split('.').pop()?.toLowerCase() || '';
        const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'tiff'];
        const resourceType = imageExts.includes(ext) ? 'image' : 'raw';

        return new Promise((resolve, reject) => {
            const uploadStream = cloudinary_1.v2.uploader.upload_stream({
                resource_type: resourceType,
                public_id: publicId,
                folder: this.options_?.folderName || undefined,
            }, (error, result) => {
                console.log({ result });
                if (error)
                    return reject(error);
                if (!result)
                    return reject(new Error("No result returned from Cloudinary upload."));
                resolve({
                    url: result.secure_url,
                    key: result.public_id.replace(new RegExp("^" + (this.options_?.folderName || "") + "/?"), ""),
                });
            });
            stream_1.Readable.from(buffer).pipe(uploadStream);
        });
    }
    async delete(file) {
        const publicId = (this.options_?.folderName ? `${this.options_?.folderName}/` : "") +
            file.fileKey.replace(/\.[^/.]+$/, "");
        console.log({ publicId });
        await cloudinary_1.v2.uploader
            .destroy(publicId)
            .then((result) => console.log(result));
        return;
    }
    async getAsBuffer(file) {
        const url = cloudinary_1.v2.url(file.fileKey, { secure: true });
        const response = await fetch(url);
        return Buffer.from(await response.arrayBuffer());
    }
    async getDownloadStream(file) {
        const url = cloudinary_1.v2.url(file.fileKey, { secure: true });
        const response = await fetch(url);
        return stream_1.Readable.fromWeb(response.body);
    }
    async getPresignedDownloadUrl(file) {
        return cloudinary_1.v2.url(file.fileKey, { secure: true });
    }
    // helper function
    cleanFilename(filename) {
        // Keep the file extension so Cloudinary detects the file type
        return filename
            .replace(/[^a-zA-Z0-9.\-_]/g, "_")
            .replace(/_+/g, "_")
            .replace(/^_+|_+$/g, "")
            .toLowerCase();
    }
    generatePublicId(filename) {
        const cleaned = this.cleanFilename(filename);
        const unique = (0, uuid_1.v4)();
        return `${unique}_${cleaned}`;
    }
}
CloudinaryFileProviderService.identifier = "cloudinary";
exports.default = CloudinaryFileProviderService;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoic2VydmljZS5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uLy4uLy4uL3NyYy9wcm92aWRlcnMvZmlsZS1jbG91ZGluYXJ5L3NlcnZpY2UudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6Ijs7QUFBQSxxREFHbUM7QUFPbkMsMkNBQThDO0FBQzlDLG1DQUFrQztBQUNsQywrQkFBb0M7QUFjcEMsTUFBTSw2QkFBOEIsU0FBUSxtQ0FBMkI7SUFLdEUsWUFBWSxFQUFFLE1BQU0sRUFBd0IsRUFBRSxPQUFnQjtRQUM3RCxLQUFLLEVBQUUsQ0FBQztRQUNSLElBQUksQ0FBQyxPQUFPLEdBQUcsTUFBTSxDQUFDO1FBQ3RCLElBQUksQ0FBQyxRQUFRLEdBQUcsT0FBTyxDQUFDO1FBRXhCLGVBQVUsQ0FBQyxNQUFNLENBQUM7WUFDakIsVUFBVSxFQUFFLE9BQU8sQ0FBQyxTQUFTO1lBQzdCLE9BQU8sRUFBRSxPQUFPLENBQUMsTUFBTTtZQUN2QixVQUFVLEVBQUUsT0FBTyxDQUFDLFNBQVM7WUFDN0IsTUFBTSxFQUFFLE9BQU8sQ0FBQyxNQUFNLElBQUksSUFBSTtTQUM5QixDQUFDLENBQUM7SUFDSixDQUFDO0lBRUQsTUFBTSxDQUFDLGVBQWUsQ0FBQyxPQUFnQjtRQUN0QyxJQUFJLENBQUMsT0FBTyxDQUFDLE1BQU0sSUFBSSxDQUFDLE9BQU8sQ0FBQyxTQUFTLElBQUksQ0FBQyxPQUFPLENBQUMsU0FBUyxFQUFFLENBQUM7WUFDakUsTUFBTSxJQUFJLG1CQUFXLENBQ3BCLG1CQUFXLENBQUMsS0FBSyxDQUFDLFlBQVksRUFDOUIscUZBQXFGLENBQ3JGLENBQUM7UUFDSCxDQUFDO0lBQ0YsQ0FBQztJQUVELEtBQUssQ0FBQyxNQUFNLENBQUMsSUFBMkI7UUFDdkMsTUFBTSxRQUFRLEdBQUcsSUFBSSxDQUFDLGdCQUFnQixDQUFDLElBQUksQ0FBQyxRQUFRLENBQUMsQ0FBQztRQUV0RCxPQUFPLENBQUMsR0FBRyxDQUFDLEVBQUUsUUFBUSxFQUFF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