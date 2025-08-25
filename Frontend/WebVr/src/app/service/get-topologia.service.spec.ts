import { TestBed } from '@angular/core/testing';

import { GetTopologiaService } from './get-topologia.service';

describe('GetTopologiaService', () => {
  let service: GetTopologiaService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(GetTopologiaService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
