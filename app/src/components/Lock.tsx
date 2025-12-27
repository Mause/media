export class Lock {
  resolve!: () => void;
  promise: Promise<void>;
  constructor() {
    this.promise = new Promise<void>((_resolve) => {
      this.resolve = _resolve;
    });
  }
  release() {
    this.resolve();
  }
  wait() {
    return this.promise;
  }
}
