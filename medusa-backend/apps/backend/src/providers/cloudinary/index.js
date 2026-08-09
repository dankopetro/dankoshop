"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const service_1 = require("./service");
const utils_1 = require("@medusajs/framework/utils");
exports.default = (0, utils_1.ModuleProvider)(utils_1.Modules.FILE, {
    services: [service_1.default],
});
