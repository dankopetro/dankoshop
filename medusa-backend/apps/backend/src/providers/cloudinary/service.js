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
        const files = Array.isArray(file) ? file : [file];
        const folder = this.options_?.folderName || "";
        for (const f of files) {
            const key = (f?.fileKey || "").replace(/^\//, "");
            if (!key) {
                continue;
            }
            const withExt = folder ? `${folder}/${key}` : key;
            let result = await cloudinary_1.v2.uploader.destroy(withExt);
            if (result?.result === "not found") {
                const withoutExt = withExt.replace(/\.[^/.]+$/, "");
                if (withoutExt !== withExt) {
                    result = await cloudinary_1.v2.uploader.destroy(withoutExt);
                }
            }
            console.log({ publicId: withExt, destroy: result });
        }
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
