

docker:
	docker build . -t aorta
	docker build . -f Dockerfile.router -t aorta-router
	docker build . -f Dockerfile.publisher -t aorta-publisher


image-push:
	docker build . -t aorta
	docker tag aorta ibrbops/aorta:latest\
		&& docker push ibrbops/aorta:latest
	docker build . -f Dockerfile.router -t aorta-router
	docker tag aorta-router ibrbops/aorta-router:latest\
		&& docker push ibrbops/aorta-router:latest
	docker build . -f Dockerfile.publisher -t aorta-publisher
	docker tag aorta-publisher ibrbops/aorta-publisher:latest\
		&& docker push ibrbops/aorta-publisher:latest
